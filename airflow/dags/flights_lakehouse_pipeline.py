from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

JOBS = "/opt/airflow/spark_jobs"

with DAG(
    dag_id="flights_lakehouse_pipeline",
    description="Kafka -> bronze -> silver -> gold (Delta Lake)",
    start_date=datetime(2026, 11, 1),
    schedule="*/10 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=1)},
    tags=["flights", "lakehouse"],
) as dag:
    bronze = BashOperator(task_id="bronze_ingest", bash_command=f"cd {JOBS} && python bronze_ingest.py")
    silver = BashOperator(task_id="silver_transform", bash_command=f"cd {JOBS} && python silver_transform.py")
    gold = BashOperator(task_id="gold_marts", bash_command=f"cd {JOBS} && python gold_marts.py")

    bronze >> silver >> gold
