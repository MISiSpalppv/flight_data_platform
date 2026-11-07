from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="reference_airports",
    description="Загрузка справочника аэропортов OurAirports в bronze и silver",
    start_date=datetime(2026, 11, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["flights", "reference"],
) as dag:
    BashOperator(task_id="load_airports", bash_command="cd /opt/airflow/spark_jobs && python ref_airports.py")
