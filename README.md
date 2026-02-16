# Tutorial Pipeline Weather

Pipeline ETL de clima com Airflow + PostgreSQL, usando a API OpenWeather.

## Objetivo
Executar um fluxo `extract -> transform -> load`:
- `extract`: consulta a API e salva JSON bruto.
- `transform`: normaliza os dados e gera um parquet intermediario.
- `load`: grava no banco PostgreSQL da aplicacao.

## Arquitetura
- Airflow executa e orquestra a DAG `weather_pipeline`.
- `postgres` (container): banco de metadados do Airflow.
- `weather-postgres` (container): banco da pipeline (`weather_data`).
- `redis`: broker do CeleryExecutor.

## Estrutura do projeto
```text
.
├── config/
│   └── .env
├── dags/
│   └── weather_dag.py
├── src/
│   ├── extract_data.py
│   ├── transform_data.py
│   └── load_data.py
├── data/
├── docker-compose.yaml
└── README.md
```

## Pre-requisitos
- Docker + Docker Compose
- (Opcional) Python 3.12 para executar scripts locais

## Configuracao
Edite `config/.env` com sua API key e credenciais do banco da aplicacao:

```env
api_key='SUA_API_KEY'
WEATHER_DB_HOST='weather-postgres'
WEATHER_DB_PORT='5432'
WEATHER_DB_NAME='weather_data'
WEATHER_DB_USER='admin'
WEATHER_DB_PASSWORD='admin'
```

## Subir o ambiente
```bash
docker compose up -d
```

Servicos principais:
- Airflow UI: `http://localhost:8080`
- Postgres da aplicacao (host local): `localhost:5433`

## Executar a DAG
1. Abra o Airflow em `http://localhost:8080`.
2. Ative a DAG `weather_pipeline`.
3. Clique em `Trigger DAG`.
4. Confira as tasks `extract`, `transform` e `load` em `success`.

## Validar dados no banco da aplicacao
Parametros de conexao:

```text
host: localhost
port: 5433
database: weather_data
user: admin
password: admin
```

Tabela carregada pela DAG:
- `the_weather`

## Problemas comuns
- Erro `Connection refused` no `load`:
  Isso acontece quando a app tenta conectar em `localhost` de dentro do container. O host correto entre containers e `weather-postgres`.
- DAG nao aparece no Airflow:
  Verifique o mount de `./dags:/opt/airflow/dags` e se o arquivo `dags/weather_dag.py` esta sem erro de sintaxe.

## Guia tecnico detalhado
Para entender o por que de cada etapa e como replicar em novos projetos:
- `GUIA_ETL_DOCKER_AIRFLOW.md`
