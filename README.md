# Flight Data Platform

Учебный проект по дисциплине «Проектирование систем обработки больших данных»:
data-платформа для анализа воздушного движения в реальном времени с Lakehouse-хранилищем и ИИ-агентом.

## Идея

Открытый ADS-B API (adsb.lol) опрашивается продюсером, события летят в Kafka, Spark складывает их
в Delta Lake на S3-хранилище (SeaweedFS) по слоям bronze → silver → gold, Airflow управляет расписанием,
а Streamlit-приложение показывает дашборды и даёт задавать вопросы ИИ-агенту на локальной LLM (Ollama).

## Архитектура

```
adsb.lol API ──► Producer ──► Kafka (flights.raw) ──► Spark ──► Bronze (Delta, S3)
                                                                   │
                                      Airflow (оркестрация)        ▼
                                                              Silver (очистка, типы, дедупликация)
                                                                   │
                                                                   ▼
                                                              Gold (7 витрин)
                                                                   │
                                                  ┌────────────────┴───────────────┐
                                                  ▼                                ▼
                                          Streamlit-дашборды              ИИ-агент (Ollama, text-to-SQL)
```

| Требование ТЗ            | Реализация                                                         |
|--------------------------|--------------------------------------------------------------------|
| Lakehouse по слоям       | Delta Lake на SeaweedFS (S3): bronze / silver / gold               |
| Движок обработки         | Apache Spark (PySpark, Structured Streaming + batch)               |
| Брокер сообщений         | Apache Kafka (KRaft) + Kafka UI                                    |
| Оркестрация              | Apache Airflow                                                     |
| Внешний источник данных  | adsb.lol (ADS-B, живые данные) + справочник аэропортов OurAirports |
| Витрины                  | Delta-таблицы слоя gold                                            |
| ИИ-агент                 | Streamlit + Ollama (qwen3:8b), запросы к витринам через DuckDB     |

## Витрины (gold)

| Витрина                    | Содержание                                              |
|----------------------------|---------------------------------------------------------|
| mart_live_aircraft         | текущие позиции самолётов за последние 10 минут          |
| mart_traffic_region_hour   | почасовой трафик по регионам                             |
| mart_airline_activity      | борты и рейсы авиакомпаний по дням                       |
| mart_aircraft_types        | статистика по типам воздушных судов                      |
| mart_aircraft_daily        | сводка по каждому борту за день                          |
| mart_emergency_events      | аварийные сигналы (squawk 7500 / 7600 / 7700)            |
| mart_airport_activity      | прилёты и вылеты у аэропортов (справочник OurAirports)   |

## Требования

- Docker Desktop (для стека рекомендуется выделить Docker не менее 8 ГБ ОЗУ)
- Ollama на хосте с моделью `qwen3:8b` (`ollama pull qwen3:8b`), для видеокарты с 6 ГБ подойдёт и `qwen3:4b-instruct`

## Запуск

```bash
cp .env.example .env
```

В `.env` замените `AIRFLOW_FERNET_KEY` на свой ключ:

```bash
python -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

```bash
docker compose up -d --build
```

Через 5–10 минут пройдёт первый запуск DAG, и витрины появятся в gold.

| Сервис          | Адрес                  | Доступ                                  |
|-----------------|------------------------|-----------------------------------------|
| Дашборд и агент | http://localhost:8501  |                                         |
| Airflow         | http://localhost:8081  | `AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD` из `.env` |
| Kafka UI        | http://localhost:8080  |                                         |
| Файлы lakehouse | http://localhost:8888  | каталог `buckets/lakehouse`             |

## Структура репозитория

```
producer/        продюсер: ADS-B API -> Kafka
spark_jobs/      Spark-задания: bronze_ingest, silver_transform, gold_marts, ref_airports
airflow/dags/    DAG-и оркестрации
app/             Streamlit-приложение и ИИ-агент
docker/          Dockerfile и вспомогательные файлы сервисов
report/          генераторы скриншотов, отчёта и презентации
```
