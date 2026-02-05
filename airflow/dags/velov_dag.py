from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from velov_extract import VeloVExtractor

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=30),
}

def trigger_extraction():
    extractor = VeloVExtractor()
    extractor.run()

with DAG(
    'velov_realtime_fetch',
    default_args=default_args,
    description='Fetch Velo\'v station data every 5 minutes',
    schedule_interval='*/5 * * * *',  # Every 5 minutes
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    fetch_task = PythonOperator(
        task_id='fetch_and_load_velov',
        python_callable=trigger_extraction,
    )