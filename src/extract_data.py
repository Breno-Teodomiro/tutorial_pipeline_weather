import requests
import json
from pathlib import Path

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = '04f8114a79f8cef5db24e8e6ba5461e3'
url = f'https://api.openweathermap.org/data/2.5/weather?q=Teresina,BR&units=metric&appid={API_KEY}'

def extract_weather_data(url: str) -> dict | list:
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        logging.error("Erro na requisição!")
        return []
    
    if not data:
        logging.warning("Nenhum dado retornado!:")
        return []

    output_path = 'data/weather_data.json'
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)
    
    logging.info(f"Arquivo salvo em {output_path}")
    return data
