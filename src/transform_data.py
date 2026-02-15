# importar bibliotecas necessárias

import pandas as pd
import json
import logging
from pathlib import Path

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Caminho do arquivo JSON extraído
path_name = Path(__file__).parent.parent / 'data' / 'weather_data.json'

# Colunbas para Dropar
columns_names_to_drop = ['weather', 'weather_icon', 'sys.type']

# Dicionário para renomear colunas
columns_names_to_rename = {
        "base": "base",
        "visibility": "visibility",
        "dt": "datetime",
        "timezone": "timezone",
        "id": "city_id", 
        "name": "city_name",
        "cod": "code",
        "coord.lon": "longitude",
        "coord.lat": "latitude",
        "main.temp": "temperature",
        "main.feels_like": "feels_like",
        "main.temp_min": "temp_min",
        "main.temp_max": "temp_max",
        "main.pressure": "pressure",
        "main.humidity": "humidity",
        "main.sea_level": "sea_level",
        "main.grnd_level": "grnd_level",
        "wind.speed": "wind_speed",
        "wind.deg": "wind_deg",
        "wind.gust": "wind_gust",
        "clouds.all": "clouds", 
        "sys.type": "sys_type",                 
        "sys.id": "sys_id",                
        "sys.country": "country",                
        "sys.sunrise": "sunrise",                
        "sys.sunset": "sunset",
        # weather_id, weather_main, weather_description 
    }

# Colunas para normalizar para datetime
columns_to_normalize_datetime = ['datetime', 'sunrise', 'sunset']

# Função para criar Dataframe a partir do arquivo JSON
def create_dataframe(path_name:str) -> pd.DataFrame:
    logging.info(" => Criando Dataframe do arquivo JSON..")
    path = path_name

    if not path.exists():
        raise FileNotFoundError(f"O arquivo {path} não foi encontrado!")
    
    with open(path) as f:
        data = json.load(f)

    df = pd.json_normalize(data)
    logging.info(f"\n ✓ Dataframe criado com sucesso! {len(df)} linhas e {len(df.columns)} colunas.")
    return df

# Função para normalizar a coluna 'weather' e criar novas colunas a partir dela
def normalize_weather_columns(df: pd.DataFrame) -> pd.DataFrame:
    df_weather = pd.json_normalize(df['weather'].apply(lambda x: x[0]))

    df_weather = df_weather.rename(columns={
        'id': 'weather_id',
        'main': 'weather_main',
        'description': 'weather_description',
        'icon': 'weather_icon'
    })

    df = pd.concat([df, df_weather], axis=1)

    logging.info(f"\n ✓ Coluna 'weather' normalizadas com sucesso - {len(df.columns)} colunas.")

    return df

# Função para dropar colunas desnecessárias
def drop_columns(df: pd.DataFrame, columns_names: list[str]) -> pd.DataFrame:
    df = df.drop(columns=columns_names)
    logging.info(f"\n ✓ Colunas {columns_names} removidas com sucesso - {len(df.columns)} colunas.")
    return df

# Função para renomear colunas
def rename_columns(df: pd.DataFrame, columns_names:dict[str, str]) -> pd.DataFrame:
    logging.info(f"\n→ Renomeando {len(columns_names)} colunas...")
    df = df.rename(columns=columns_names)
    logging.info("✓ Colunas renomeadas")
    return df 
    
# Função para converter colunas de timestamp para datetime    
def normalize_datetime_columns(df: pd.DataFrame, columns_names:list[str]) -> pd.DataFrame:
    logging.info(f"\n→ Convertendo colunas para datetime: {columns_names}")
    for name in columns_names:
        df[name] = pd.to_datetime(df[name], unit='s', utc=True).dt.tz_convert('America/Sao_Paulo')
    logging.info("✓ Colunas convertidas para datetime\n")    
    return df

# Função para chamar as funções que realizam todas as transformações
def data_transformations():
    print("\n Iniciando transformações")
    df = create_dataframe(path_name)
    df = normalize_weather_columns(df)
    df = drop_columns(df, columns_names_to_drop)
    df = rename_columns(df, columns_names_to_rename)
    df = normalize_datetime_columns(df, columns_to_normalize_datetime)
    logging.info("✓ Transformações concluídas\n")
    return df
