import logging
import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

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


def ensure_dw_structure() -> None:
    engine = get_engine()
    ddl_statements = [
        "CREATE SCHEMA IF NOT EXISTS raw",
        "CREATE SCHEMA IF NOT EXISTS intermediate",
        "CREATE SCHEMA IF NOT EXISTS mart",
        """
        CREATE TABLE IF NOT EXISTS raw.weather_observations (
            city_id BIGINT NOT NULL,
            city_name TEXT NOT NULL,
            country TEXT,
            datetime TIMESTAMPTZ NOT NULL,
            sunrise TIMESTAMPTZ,
            sunset TIMESTAMPTZ,
            weather_id INTEGER,
            weather_main TEXT,
            weather_description TEXT,
            temperature DOUBLE PRECISION,
            feels_like DOUBLE PRECISION,
            temp_min DOUBLE PRECISION,
            temp_max DOUBLE PRECISION,
            pressure INTEGER,
            humidity INTEGER,
            sea_level INTEGER,
            grnd_level INTEGER,
            wind_speed DOUBLE PRECISION,
            wind_deg DOUBLE PRECISION,
            wind_gust DOUBLE PRECISION,
            clouds INTEGER,
            visibility INTEGER,
            timezone INTEGER,
            code INTEGER,
            base TEXT,
            longitude DOUBLE PRECISION,
            latitude DOUBLE PRECISION,
            sys_id BIGINT,
            ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            source_name TEXT NOT NULL DEFAULT 'openweather_api',
            CONSTRAINT uq_weather_observations_city_dt UNIQUE (city_id, datetime)
        )
        """,
    ]

    with engine.begin() as conn:
        for ddl in ddl_statements:
            conn.execute(text(ddl))

    logging.info("✅ Estrutura DW garantida (raw/intermediate/mart).")


def _prepare_raw_records(df: pd.DataFrame) -> list[dict]:
    nullable_columns = [
        "country",
        "sunrise",
        "sunset",
        "weather_id",
        "weather_main",
        "weather_description",
        "temperature",
        "feels_like",
        "temp_min",
        "temp_max",
        "pressure",
        "humidity",
        "sea_level",
        "grnd_level",
        "wind_speed",
        "wind_deg",
        "wind_gust",
        "clouds",
        "visibility",
        "timezone",
        "code",
        "base",
        "longitude",
        "latitude",
        "sys_id",
    ]

    mandatory_columns = ["city_id", "city_name", "datetime"]
    for col in mandatory_columns:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatoria ausente para carga RAW: {col}")

    records = []
    for _, row in df.iterrows():
        record = {
            "city_id": int(row["city_id"]),
            "city_name": str(row["city_name"]),
            "datetime": row["datetime"].to_pydatetime() if hasattr(row["datetime"], "to_pydatetime") else row["datetime"],
        }
        for col in nullable_columns:
            value = row[col] if col in row else None
            if pd.isna(value):
                value = None
            record[col] = value
        records.append(record)

    return records


def load_weather_data(table_name: str, df: pd.DataFrame) -> None:
    if table_name != "weather_observations":
        logging.info(
            "Tabela '%s' ignorada. A carga DW padrao utiliza raw.weather_observations.",
            table_name,
        )
    load_weather_to_raw(df)


def load_weather_to_raw(df: pd.DataFrame) -> None:
    ensure_dw_structure()
    engine = get_engine()
    records = _prepare_raw_records(df)

    if not records:
        logging.warning("Nenhum registro para carregar na camada RAW.")
        return

    upsert_sql = text(
        """
        INSERT INTO raw.weather_observations (
            city_id, city_name, country, datetime, sunrise, sunset,
            weather_id, weather_main, weather_description, temperature,
            feels_like, temp_min, temp_max, pressure, humidity, sea_level,
            grnd_level, wind_speed, wind_deg, wind_gust, clouds, visibility,
            timezone, code, base, longitude, latitude, sys_id
        )
        VALUES (
            :city_id, :city_name, :country, :datetime, :sunrise, :sunset,
            :weather_id, :weather_main, :weather_description, :temperature,
            :feels_like, :temp_min, :temp_max, :pressure, :humidity, :sea_level,
            :grnd_level, :wind_speed, :wind_deg, :wind_gust, :clouds, :visibility,
            :timezone, :code, :base, :longitude, :latitude, :sys_id
        )
        ON CONFLICT (city_id, datetime)
        DO UPDATE SET
            city_name = EXCLUDED.city_name,
            country = EXCLUDED.country,
            sunrise = EXCLUDED.sunrise,
            sunset = EXCLUDED.sunset,
            weather_id = EXCLUDED.weather_id,
            weather_main = EXCLUDED.weather_main,
            weather_description = EXCLUDED.weather_description,
            temperature = EXCLUDED.temperature,
            feels_like = EXCLUDED.feels_like,
            temp_min = EXCLUDED.temp_min,
            temp_max = EXCLUDED.temp_max,
            pressure = EXCLUDED.pressure,
            humidity = EXCLUDED.humidity,
            sea_level = EXCLUDED.sea_level,
            grnd_level = EXCLUDED.grnd_level,
            wind_speed = EXCLUDED.wind_speed,
            wind_deg = EXCLUDED.wind_deg,
            wind_gust = EXCLUDED.wind_gust,
            clouds = EXCLUDED.clouds,
            visibility = EXCLUDED.visibility,
            timezone = EXCLUDED.timezone,
            code = EXCLUDED.code,
            base = EXCLUDED.base,
            longitude = EXCLUDED.longitude,
            latitude = EXCLUDED.latitude,
            sys_id = EXCLUDED.sys_id,
            ingested_at = NOW()
        """
    )

    with engine.begin() as conn:
        conn.execute(upsert_sql, records)

    logging.info("✅ Dados carregados na camada RAW com upsert incremental.")

    df_check = pd.read_sql("SELECT COUNT(*) AS total FROM raw.weather_observations", con=engine)
    total = int(df_check.iloc[0]["total"])
    logging.info("Total de registros em raw.weather_observations: %s", total)
