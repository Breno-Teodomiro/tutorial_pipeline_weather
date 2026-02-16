# Tutorial Pipeline Weather

Pipeline de dados climáticos com Airflow, PostgreSQL e dbt, estruturada em camadas de DW:
- `raw`
- `intermediate`
- `mart`

## Arquitetura
- `extract` (Python): consome OpenWeather e salva JSON bruto.
- `transform` (Python): normaliza JSON em DataFrame.
- `load` (Python): faz `upsert` incremental em `raw.weather_observations`.
- `build_dw` (dbt): transforma `raw -> intermediate -> mart`.

Orquestração:
- DAG `weather_pipeline`: `extract >> transform >> load >> build_dw`.

Infra:
- `postgres`: metadados do Airflow.
- `weather-postgres`: banco analítico do projeto (`weather_data`).
- `redis`: broker do Celery.

## Estrutura
```text
.
├── config/
│   ├── .env.example
│   └── .env (local, nao versionado)
├── dags/
│   └── weather_dag.py
├── src/
│   ├── extract_data.py
│   ├── transform_data.py
│   ├── load_data.py
│   └── dbt_runner.py
├── dbt_weather/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/
│       ├── intermediate/
│       └── marts/
├── docker-compose.yaml
└── README.md
```

## Configuracao
1. Crie `config/.env` a partir do exemplo:
```bash
cp config/.env.example config/.env
```

2. Preencha sua API key no `config/.env`:
```env
api_key='SUA_API_KEY'
WEATHER_DB_HOST='weather-postgres'
WEATHER_DB_PORT='5432'
WEATHER_DB_NAME='weather_data'
WEATHER_DB_USER='admin'
WEATHER_DB_PASSWORD='admin'
```

## Subir ambiente
```bash
docker compose up -d
```

URLs/portas:
- Airflow: `http://localhost:8080`
- PostgreSQL analítico: `localhost:5433`

## Camadas do DW
### `raw`
- Tabela: `raw.weather_observations`
- Estratégia: `upsert` incremental por `(city_id, datetime)`.

### `intermediate`
- Modelo dbt: `intermediate.int_weather_observations`
- Padronização e colunas derivadas em português (`hora_observacao`, `data_referencia`, `chave_grao_clima`).
- Datas padronizadas para horário local de Brasília (`America/Sao_Paulo`), sem offset.

### `mart`
- `mart.mart_weather_readings` (incremental): pronto para fatos no Power BI.
- `mart.mart_weather_daily_city` (view): agregações diárias por cidade.
- Datas de consumo em horário de Brasília (ideal para visualização no Power BI).
- Coluna adicional `data_observacao_formatada` no padrão `YYYY-MM-DD HH24:MI:SS`.

## Como executar
1. Ative a DAG `weather_pipeline` no Airflow.
2. Faça `Trigger DAG`.
3. Verifique as tasks em `success`: `extract`, `transform`, `load`, `build_dw`.

## Consultas de validação
```sql
-- RAW
SELECT count(*) FROM raw.weather_observations;

-- INTERMEDIATE
SELECT count(*) FROM intermediate.int_weather_observations;

-- MART
SELECT count(*) FROM mart.mart_weather_readings;
SELECT * FROM mart.mart_weather_daily_city ORDER BY data_referencia DESC LIMIT 20;

-- Validar formato horário Brasil (sem offset) na mart
SELECT data_observacao
FROM mart.mart_weather_readings
ORDER BY data_observacao DESC
LIMIT 5;

-- Validar string formatada (YYYY-MM-DD HH:MM:SS)
SELECT data_observacao_formatada
FROM mart.mart_weather_readings
ORDER BY data_observacao DESC
LIMIT 5;
```

## Documentação dbt
```bash
docker compose exec -T airflow-scheduler dbt docs generate \
  --project-dir /opt/airflow/dbt_weather \
  --profiles-dir /opt/airflow/dbt_weather \
  --target dev
```

Guia completo da parte dbt:
- `GUIA_DBT_WEATHER.md`

## Guias do projeto
- `GUIA_COMPLETO_PROJETO.md` -> onboarding completo (iniciante ao avançado)
- `GUIA_ETL_DOCKER_AIRFLOW.md` -> fundamentos técnicos de ETL + Airflow + Docker
- `GUIA_DBT_WEATHER.md` -> modelagem dbt, testes e documentação

## Observações
- O `dbt` roda dentro do Airflow via task Python (`src/dbt_runner.py`).
- Dependências dbt são instaladas no startup dos containers via `_PIP_ADDITIONAL_REQUIREMENTS`.
- Para ambiente de produção, recomenda-se imagem customizada do Airflow com dbt pré-instalado.
