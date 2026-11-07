import os

import duckdb
import pandas as pd
from deltalake import DeltaTable

BUCKET = os.getenv("LAKE_BUCKET", "lakehouse")

MARTS = {
    "mart_live_aircraft": "Последняя известная позиция каждого самолёта за последние 10 минут: координаты, высота (футы), скорость (узлы), курс, вертикальная скорость, признак нахождения на земле.",
    "mart_traffic_region_hour": "Почасовой трафик по регионам: число уникальных самолётов, количество сообщений, средняя высота и скорость, число сообщений с земли.",
    "mart_airline_activity": "Активность авиакомпаний по дням (airline_code - ICAO-код из позывного, например DLH, BAW, UAL): число самолётов и рейсов, средняя скорость и высота.",
    "mart_aircraft_types": "Статистика по типам воздушных судов (aircraft_type - ICAO-код типа, например A320, B738): число бортов, средняя и максимальная скорость, максимальная высота.",
    "mart_aircraft_daily": "Сводка по каждому борту за день: позывной, регистрация, тип, первое и последнее появление, максимальные высота и скорость, число посещённых регионов.",
    "mart_emergency_events": "Аварийные сигналы: squawk 7500 (угон), 7600 (потеря связи), 7700 (общая авария) и поле emergency.",
    "mart_airport_activity": "Почасовая активность вокруг аэропортов (радиус 12 км): самолёты рядом, на земле, на снижении (прилёты) и на наборе высоты (вылеты). Данные OurAirports.",
}


def storage_options():
    return {
        "AWS_ENDPOINT_URL": os.environ["S3_ENDPOINT"],
        "AWS_ACCESS_KEY_ID": os.environ["S3_ACCESS_KEY"],
        "AWS_SECRET_ACCESS_KEY": os.environ["S3_SECRET_KEY"],
        "AWS_REGION": "us-east-1",
        "AWS_ALLOW_HTTP": "true",
        "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
    }


def load_mart(name):
    table = DeltaTable(f"s3://{BUCKET}/gold/{name}", storage_options=storage_options())
    df = table.to_pandas()
    if "on_ground" in df.columns:
        df["on_ground"] = df["on_ground"].fillna(False).astype(bool)
    return df


def available_marts():
    found = {}
    for name in MARTS:
        try:
            found[name] = load_mart(name)
        except Exception:
            continue
    return found


def connect(marts):
    con = duckdb.connect()
    for name, df in marts.items():
        con.register(name, df)
    return con


def schema_description(marts):
    lines = []
    for name, df in marts.items():
        cols = ", ".join(f"{c} ({str(t)})" for c, t in df.dtypes.items())
        lines.append(f"Таблица {name}: {MARTS[name]}\n  Колонки: {cols}")
    return "\n".join(lines)


def run_sql(con, sql):
    return con.execute(sql).fetchdf()
