import os
import re

import requests

from lake import run_sql, schema_description

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

SQL_SYSTEM = """Ты аналитик данных. Тебе нужно превратить вопрос пользователя в один SQL-запрос для DuckDB.
Доступны только эти таблицы (витрины lakehouse, данные о воздушном движении ADS-B):

{schema}

Правила:
- Верни только один SELECT-запрос внутри блока ```sql ... ```, без пояснений.
- Используй только перечисленные таблицы и колонки.
- Всегда добавляй LIMIT не больше 50.
- Высота в футах, скорость в узлах, время в UTC.
- Если вопрос нельзя решить этими данными, верни запрос SELECT 'нет данных' AS ответ.
- Одна строка витрины mart_aircraft_types уже означает один тип; "чаще всего" считай по unique_aircraft.
- Колонка on_ground булева: используй NOT on_ground или on_ground = false.
- Не используй UNION, пиши простые запросы.

Примеры:
Вопрос: Какие 3 типа самолётов самые популярные?
```sql
SELECT aircraft_type, aircraft_desc, unique_aircraft FROM mart_aircraft_types ORDER BY unique_aircraft DESC LIMIT 3
```
Вопрос: Сколько самолётов сейчас в воздухе по регионам?
```sql
SELECT region, COUNT(*) AS airborne FROM mart_live_aircraft WHERE NOT on_ground GROUP BY region ORDER BY airborne DESC LIMIT 50
```
Вопрос: Были ли аварийные сигналы?
```sql
SELECT position_ts, callsign, region, reason FROM mart_emergency_events ORDER BY position_ts DESC LIMIT 20
```
"""

ANSWER_SYSTEM = """Ты помощник-аналитик воздушного движения. Ответь на вопрос пользователя по-русски, кратко и только на основе результата SQL-запроса.
Не выдумывай данные, которых нет в результате. Если результат пустой, так и скажи."""


def chat(messages, temperature=0.1):
    resp = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {"temperature": temperature, "num_ctx": 4096},
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def extract_sql(text):
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S | re.I)
    sql = (match.group(1) if match else text).strip().rstrip(";")
    return sql


def is_safe(sql):
    lowered = sql.lower()
    forbidden = ("insert", "update", "delete", "drop", "alter", "create", "attach", "copy", "pragma", "install", "load")
    return lowered.startswith(("select", "with")) and not any(re.search(rf"\b{w}\b", lowered) for w in forbidden)


def ask(question, con, marts):
    schema = schema_description(marts)
    sql_text = chat([
        {"role": "system", "content": SQL_SYSTEM.format(schema=schema)},
        {"role": "user", "content": question},
    ], temperature=0.0)
    sql = extract_sql(sql_text)

    error = None
    result = None
    for attempt in range(2):
        if not is_safe(sql):
            error = "Запрос отклонён: разрешены только SELECT"
            break
        try:
            result = run_sql(con, sql)
            error = None
            break
        except Exception as exc:
            error = str(exc)
            if attempt == 0:
                fixed = chat([
                    {"role": "system", "content": SQL_SYSTEM.format(schema=schema)},
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": f"```sql\n{sql}\n```"},
                    {"role": "user", "content": f"Запрос завершился ошибкой: {error}. Исправь запрос."},
                ], temperature=0.0)
                sql = extract_sql(fixed)

    if error:
        return {"sql": sql, "data": None, "answer": f"Не удалось выполнить запрос: {error}"}

    preview = result.head(30).to_markdown(index=False) if len(result) else "(пустой результат)"
    answer = chat([
        {"role": "system", "content": ANSWER_SYSTEM},
        {"role": "user", "content": f"Вопрос: {question}\n\nSQL:\n{sql}\n\nРезультат:\n{preview}"},
    ], temperature=0.2)
    return {"sql": sql, "data": result, "answer": answer}
