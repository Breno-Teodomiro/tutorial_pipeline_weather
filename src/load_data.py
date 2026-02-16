import logging
import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
load_dotenv(env_path)


def _get_database_settings() -> dict[str, str]:
    # Mantem retrocompatibilidade com as chaves antigas do .env.
    database = os.getenv("WEATHER_DB_NAME") or os.getenv("database", "weather_data")
    user = os.getenv("WEATHER_DB_USER") or os.getenv("user", "admin")
    password = os.getenv("WEATHER_DB_PASSWORD") or os.getenv("password", "admin")
    host = os.getenv("WEATHER_DB_HOST") or os.getenv("host", "weather-postgres")
    port = os.getenv("WEATHER_DB_PORT", "5432")

    return {
        "database": database,
        "user": user,
        "password": password,
        "host": host,
        "port": port,
    }


@lru_cache(maxsize=1)
def get_engine():
    settings = _get_database_settings()
    logging.info(
        "→ Conectando em %s:%s/%s",
        settings["host"],
        settings["port"],
        settings["database"],
    )
    return create_engine(
        "postgresql+psycopg2://"
        f"{settings['user']}:{quote_plus(settings['password'])}@"
        f"{settings['host']}:{settings['port']}/{settings['database']}",
        pool_pre_ping=True,
    )


def load_weather_data(table_name: str, df: pd.DataFrame) -> None:
    engine = get_engine()

    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
    )

    logging.info("✅ Dados carregados com sucesso!")

    df_check = pd.read_sql(f"SELECT * FROM {table_name}", con=engine)
    logging.info("Total de registros na tabela %s: %s", table_name, len(df_check))
