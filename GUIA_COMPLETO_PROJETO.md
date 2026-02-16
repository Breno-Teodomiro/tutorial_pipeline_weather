# Guia Completo do Projeto (Iniciantes)

Este guia explica o projeto de ponta a ponta, com comandos práticos e o motivo de cada etapa.

## 1) O que este projeto faz
Pipeline de clima com arquitetura moderna de dados:
- Orquestração: Airflow
- Banco: PostgreSQL
- Transformações analíticas: dbt
- Camadas DW: `raw`, `intermediate`, `mart`

Fluxo da DAG:
1. `extract` -> busca dados da API OpenWeather
2. `transform` -> normaliza JSON em DataFrame
3. `load` -> grava incremental na `raw`
4. `build_dw` -> dbt cria/atualiza `intermediate` e `mart`

## 2) Pré-requisitos
- Docker + Docker Compose instalados
- Git
- Conta e API key da OpenWeather

## 3) Estrutura principal
```text
.
├── config/.env.example            # exemplo de variáveis
├── config/.env                    # local, não versionado
├── dags/weather_dag.py            # DAG do Airflow
├── src/                           # lógica Python (extract/transform/load/dbt_runner)
├── dbt_weather/                   # projeto dbt
├── docker-compose.yaml            # infra local
└── README.md
```

## 4) Setup inicial (primeira vez)
1. Clonar:
```bash
git clone https://github.com/Breno-Teodomiro/tutorial_pipeline_weather.git
cd tutorial_pipeline_weather
```

2. Criar arquivo de ambiente:
```bash
cp config/.env.example config/.env
```

3. Editar `config/.env` e preencher:
```env
api_key='SUA_API_KEY'
WEATHER_DB_HOST='weather-postgres'
WEATHER_DB_PORT='5432'
WEATHER_DB_NAME='weather_data'
WEATHER_DB_USER='admin'
WEATHER_DB_PASSWORD='admin'
```

4. Subir infraestrutura:
```bash
docker compose up -d
```

## 5) Como usar o Airflow
1. Abrir UI: `http://localhost:8080`
2. Ativar DAG `weather_pipeline`
3. Clicar em `Trigger DAG`
4. Confirmar `success` nas tasks:
   - `extract`
   - `transform`
   - `load`
   - `build_dw`

Agendamento atual da DAG:
- `*/5 * * * *` (a cada 5 minutos)

## 6) O que acontece em cada camada do DW

## 6.1 `raw`
- Tabela: `raw.weather_observations`
- Objetivo: armazenar dado mais próximo da fonte
- Estratégia: `upsert` por `(city_id, datetime)` para evitar duplicação

## 6.2 `intermediate`
- Modelo: `intermediate.int_weather_observations`
- Objetivo: padronização e enriquecimento técnico
- Colunas em português
- `data_observacao` em horário de Brasília

## 6.3 `mart`
- `mart.mart_weather_readings`: fato detalhado para dashboard
- `mart.mart_weather_daily_city`: visão agregada diária
- `data_observacao_formatada` no padrão `YYYY-MM-DD HH:MM:SS`

## 7) Timezone e formato de data (importante)
- A API fornece timestamps de referência UTC.
- O Python já converte para `America/Sao_Paulo` na transformação.
- O dbt reafirma padronização em Brasília nas camadas analíticas.
- No banco, campo `timestamp` pode aparecer com `.000` por exibição de ferramenta.
- Para formato textual fixo, use `data_observacao_formatada`.

## 8) Consultas SQL úteis
```sql
-- Contagem por camada
SELECT count(*) FROM raw.weather_observations;
SELECT count(*) FROM intermediate.int_weather_observations;
SELECT count(*) FROM mart.mart_weather_readings;

-- Leitura analítica final
SELECT *
FROM mart.mart_weather_readings
ORDER BY data_observacao DESC
LIMIT 20;

-- Formato fixo para exibição
SELECT data_observacao_formatada
FROM mart.mart_weather_readings
ORDER BY data_observacao DESC
LIMIT 20;
```

## 9) Como conectar no DBeaver
Parâmetros:
- Host: `localhost`
- Port: `5433`
- Database: `weather_data`
- User: `admin`
- Password: `admin`

Schemas para explorar:
- `raw`
- `intermediate`
- `mart`

## 10) Comandos dbt no projeto
Rodar dbt:
```bash
docker compose exec -T airflow-scheduler dbt run \
  --project-dir /opt/airflow/dbt_weather \
  --profiles-dir /opt/airflow/dbt_weather \
  --target dev
```

Rodar testes:
```bash
docker compose exec -T airflow-scheduler dbt test \
  --project-dir /opt/airflow/dbt_weather \
  --profiles-dir /opt/airflow/dbt_weather \
  --target dev
```

Gerar docs:
```bash
docker compose exec -T airflow-scheduler dbt docs generate \
  --project-dir /opt/airflow/dbt_weather \
  --profiles-dir /opt/airflow/dbt_weather \
  --target dev
```

Servir docs localmente:
```bash
cd dbt_weather/target
python -m http.server 8081
```

Abrir:
- `http://localhost:8081`

## 11) Troubleshooting rápido
`Connection refused` no `load`:
- verificar se `weather-postgres` está saudável
- confirmar host `weather-postgres` no `.env`

DAG não aparece:
- verificar `dags/weather_dag.py`
- confirmar volume `./dags:/opt/airflow/dags`

Mudou modelo incremental e deu erro de coluna:
- rodar full refresh uma vez:
```bash
docker compose exec -T airflow-scheduler dbt run \
  --project-dir /opt/airflow/dbt_weather \
  --profiles-dir /opt/airflow/dbt_weather \
  --target dev \
  --full-refresh
```

## 12) Guia de estudo sugerido
Ordem recomendada para aprender este projeto:
1. `README.md` (visão rápida)
2. `GUIA_COMPLETO_PROJETO.md` (este arquivo)
3. `GUIA_ETL_DOCKER_AIRFLOW.md` (fundamentos de arquitetura)
4. `GUIA_DBT_WEATHER.md` (modelagem e documentação dbt)
