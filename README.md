# Flight Data Platform

Учебный проект по дисциплине «Проектирование систем обработки больших данных»:
data-платформа для анализа воздушного движения в реальном времени с Lakehouse-хранилищем и ИИ-агентом.

## Идея

Открытый ADS-B API (adsb.lol) опрашивается продюсером, события летят в Kafka, Spark складывает их
в Delta Lake на SeaweedFS (S3) по слоям bronze → silver → gold, Airflow управляет расписанием,
а Streamlit-приложение показывает дашборды и даёт задавать вопросы ИИ-агенту на локальной LLM (Ollama).

## Архитектура

```
adsb.lol API ──► Producer ──► Kafka (flights.raw) ──► Spark ──► Bronze (Delta, SeaweedFS (S3))
                                                                   │
                                      Airflow (оркестрация)        ▼
                                                              Silver (очистка, типы, дедупликация)
                                                                   │
                                                                   ▼
                                                              Gold (витрины)
                                                                   │
                                                  ┌────────────────┴───────────────┐
                                                  ▼                                ▼
                                          Streamlit-дашборды              ИИ-агент (Ollama, text-to-SQL)
```

| Требование ТЗ            | Реализация                                                   |
|--------------------------|--------------------------------------------------------------|
| Lakehouse по слоям       | Delta Lake на SeaweedFS (S3): bronze / silver / gold                  |
| Движок обработки         | Apache Spark (PySpark, Structured Streaming + batch)         |
| Брокер сообщений         | Apache Kafka (KRaft) + Kafka UI                              |
| Оркестрация              | Apache Airflow                                               |
| Внешний источник данных  | adsb.lol (ADS-B, живые данные) + справочник аэропортов OurAirports |
| Витрины                  | Delta-таблицы слоя gold                                      |
| ИИ-агент                 | Streamlit + Ollama (qwen3), запросы к витринам через DuckDB  |

## Запуск

```bash
cp .env.example .env
docker compose up -d --build
```

Подробности по сервисам и порядку запуска будут дополняться по мере разработки.

