from datetime import datetime, timedelta
from airflow.sdk import dag, task
from pathlib import Path
import sys
import os

sys.path.insert(0, '/opt/airflow/src')

from extract_data import extract_weather_data
from load_data import load_weather_data
from transform_data import data_transformations
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / 'config' / '.env'
load_dotenv(env_path)

API_KEY = os.getenv('api_key')
url = f'https://api.openweathermap.org/data/2.5/weather?q=Teresina,BR&units=metric&appid={API_KEY}'

@dag(
    dag_id='weather_pipeline',
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'retries': 2,
        'retry_delay': timedelta(minutes=5)
    },
    description='Pipeline ETL - Clima Teresina',
    schedule='*/5 * * * *', #Rodar de 5 em 5 minutos  '0 */1 * * *' rodar de hora em hora,
    start_date=datetime(2026, 2, 15),
    catchup=False,
    tags=['weather', 'etl', 'airflow']
)
def weather_pipeline():
    
    @task
    def extract():
        extract_weather_data(url)
        
    @task
    def transform():
        df = data_transformations()
        df.to_parquet('/opt/airflow/data/temp_data.parquet', index=False)
        
    @task 
    def load():
        import pandas as pd
        df = pd.read_parquet('/opt/airflow/data/temp_data.parquet')
        load_weather_data('the_weather', df)
        
    extract() >> transform() >> load()

weather_pipeline()
