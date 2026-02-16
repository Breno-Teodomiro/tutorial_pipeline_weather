# Guia dbt: Weather DW

Guia prático para desenvolvimento, execução e documentação do `dbt` neste projeto.

## Estrutura dbt no projeto
- Projeto: `dbt_weather/`
- Perfil: `dbt_weather/profiles.yml`
- Modelos:
  - `staging`: padronização inicial da RAW
  - `intermediate`: tratamento e granularidade analítica
  - `marts`: camadas finais para consumo no Power BI

## Convenções adotadas
- Nomenclatura das colunas em português nas camadas dbt.
- Datas das camadas `intermediate` e `mart` em horário de Brasília (`America/Sao_Paulo`), sem offset.
- `mart_weather_readings` expõe também `data_observacao_formatada` (`YYYY-MM-DD HH24:MI:SS`) para consumo visual.
- Camadas físicas no Postgres:
  - `raw`
  - `intermediate`
  - `mart`
- Incremental em:
  - `intermediate.int_weather_observations`
  - `mart.mart_weather_readings`

## Como executar dbt
### 1) Pelo Airflow (fluxo padrão)
A DAG já executa `dbt run` automaticamente na task `build_dw`.

### 2) Manualmente no container do Airflow
```bash
docker compose exec -T airflow-scheduler dbt run \
  --project-dir /opt/airflow/dbt_weather \
  --profiles-dir /opt/airflow/dbt_weather \
  --target dev
```

### 3) Rodar testes de qualidade
```bash
docker compose exec -T airflow-scheduler dbt test \
  --project-dir /opt/airflow/dbt_weather \
  --profiles-dir /opt/airflow/dbt_weather \
  --target dev
```

## Documentação do dbt
### Gerar documentação
```bash
docker compose exec -T airflow-scheduler dbt docs generate \
  --project-dir /opt/airflow/dbt_weather \
  --profiles-dir /opt/airflow/dbt_weather \
  --target dev
```

### Servir documentação localmente (host)
Depois de gerar, os arquivos ficam em `dbt_weather/target/`.

No seu host, rode:
```bash
cd dbt_weather/target
python -m http.server 8081
```

Depois, abra:
- `http://localhost:8081`

### Nota de migração de schema
Ao renomear colunas em modelos incrementais, pode ocorrer incompatibilidade com tabelas antigas.
Neste projeto, a task `build_dw` já tem fallback automático:
- tenta `dbt run`
- se detectar erro de coluna ausente, reexecuta `dbt run --full-refresh` automaticamente

## Consultas úteis para validação
```sql
-- Intermediate
select id_cidade, cidade, data_observacao, temperatura
from intermediate.int_weather_observations
order by data_observacao desc
limit 20;

-- Mart detalhada
select id_cidade, cidade, data_observacao, temperatura_celsius, umidade
from mart.mart_weather_readings
order by data_observacao desc
limit 20;

-- Conferir formato local (sem offset)
select data_observacao
from mart.mart_weather_readings
order by data_observacao desc
limit 5;

-- Conferir formato texto padrão
select data_observacao_formatada
from mart.mart_weather_readings
order by data_observacao desc
limit 5;

-- Mart agregada diária
select *
from mart.mart_weather_daily_city
order by data_referencia desc
limit 20;
```

## Boas práticas para evoluir
1. Documentar cada nova coluna em arquivos `yml`.
2. Adicionar `data_tests` para chaves e colunas críticas.
3. Manter `staging` próximo da fonte e concentrar regras de negócio em `intermediate`/`mart`.
4. Evitar lógica duplicada em dashboards; centralizar no `mart`.
