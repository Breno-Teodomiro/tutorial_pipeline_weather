# Guia Tecnico: ETL + Airflow + Docker

Este arquivo e um guia de estudo para voce reutilizar a mesma logica em novos projetos.

## 1. Visao geral do fluxo
O pipeline tem 3 etapas:
1. `extract`: busca dado externo e salva dado bruto.
2. `transform`: limpa/estrutura o dado para consumo.
3. `load`: persiste no banco final.

No Airflow, essas etapas viram tasks encadeadas:
`extract() >> transform() >> load()`.

Por que funciona:
- Cada etapa tem responsabilidade unica.
- Falhas ficam isoladas por task.
- Reprocessamento e observabilidade ficam simples.

## 2. Explicacao de cada modulo

## 2.1 `src/extract_data.py`
Responsabilidade:
- Fazer request HTTP na API OpenWeather.
- Validar retorno basico.
- Salvar em `data/weather_data.json`.

Por que essa estrategia:
- Guardar o bruto facilita auditoria e debug.
- Se der erro no `transform`, voce nao precisa chamar API de novo.

Ponto de atencao:
- Hoje nao ha timeout/retry HTTP na funcao. Em projeto maior, vale adicionar.

## 2.2 `src/transform_data.py`
Responsabilidade:
- Ler o JSON bruto.
- Achatar estrutura aninhada (`json_normalize`).
- Tratar coluna `weather` (lista de objetos).
- Remover colunas nao usadas.
- Renomear colunas para nomes de negocio.
- Converter timestamps para datetime timezone-aware.

Por que funciona:
- O dado sai da API em estrutura semi-aninhada; para analytics/SQL, o ideal e formato tabular.
- Renomear e padronizar colunas facilita leitura e manutencao.

Ponto de atencao:
- A transformacao depende da estrutura da API. Se o payload mudar, essa etapa pode quebrar.

## 2.3 `src/load_data.py`
Responsabilidade:
- Ler credenciais do `config/.env`.
- Montar engine SQLAlchemy.
- Gravar DataFrame no Postgres (`to_sql`).

Decisao importante:
- O host padrao e `weather-postgres` (nome do servico Docker), nao `localhost`.

Por que funciona:
- Dentro da rede Docker Compose, containers se comunicam pelo nome do servico.
- `localhost` dentro do container aponta para o proprio container, nao para outro servico.

Detalhe util:
- `pool_pre_ping=True` evita conexao quebrada reaproveitada no pool.

## 3. Explicacao da DAG (`dags/weather_dag.py`)
Responsabilidade:
- Orquestrar as 3 etapas.
- Definir retries, schedule e dependencias.

Campos importantes:
- `dag_id='weather_pipeline'`: nome da DAG.
- `schedule='*/5 * * * *'`: roda a cada 5 minutos.
- `retries=2`: reduz falha por erro transitorio.
- `catchup=False`: nao roda historico retroativo automaticamente.

Por que funciona:
- A DAG so define fluxo e politica de execucao.
- A logica de negocio fica em `src/`, separada do orquestrador.

## 4. Explicacao do `docker-compose.yaml`

## 4.1 Servicos principais
- `postgres`: metadados do Airflow (nao use para dado de negocio).
- `weather-postgres`: banco da aplicacao/pipeline.
- `redis`: broker para CeleryExecutor.
- `airflow-*`: webserver/api, scheduler, worker, triggerer, dag-processor e init.

## 4.2 Por que separar 2 Postgres
Separacao recomendada:
- Banco de plataforma (Airflow metadata).
- Banco de aplicacao (dados de negocio).

Beneficios:
- Evita misturar tabelas internas do Airflow com tabelas da pipeline.
- Facilita backup, governanca e manutencao.
- Reduz risco operacional ao evoluir seu dado de negocio.

## 4.3 Rede e nomes DNS no Docker
Regra pratica:
- Container A acessa container B pelo nome do servico B.

Exemplo deste projeto:
- Airflow acessa banco da pipeline com host `weather-postgres`.
- Do seu host local (fora do Docker), voce acessa pela porta publicada `localhost:5433`.

## 4.4 Volumes
- `postgres-db-volume`: persistencia dos metadados do Airflow.
- `weather-postgres-db-volume`: persistencia dos dados da aplicacao.

Por que importa:
- Sem volume, ao recriar container voce perde dados.

## 4.5 `depends_on` + `healthcheck`
O Compose espera os bancos ficarem saudaveis antes de subir servicos do Airflow.

Por que isso evita erro:
- Sem healthcheck, scheduler/worker podem iniciar antes do banco aceitar conexao.

## 5. Como replicar este padrao em outro projeto
Checklist de replicacao:
1. Defina ETL em modulos separados (`extract`, `transform`, `load`).
2. Crie DAG pequena, apenas orquestrando.
3. Use 2 bancos: plataforma e aplicacao.
4. Use `.env` para configuracoes sensiveis.
5. Configure `healthcheck` nos servicos criticos.
6. Valide conexao do `load` de dentro do container do Airflow.

## 6. Sinais de que esta tudo correto
- DAG aparece e executa no Airflow.
- Tasks finalizam em `success`.
- Tabela `the_weather` recebe registros no `weather-postgres`.
- Nao ha tentativa de conexao em `localhost:5432` dentro das tasks.

## 7. Erros comuns e como pensar no diagnostico
- `Connection refused`:
  Verifique host/porta e onde o codigo esta rodando (host local ou container).
- `Task queued` sem executar:
  Veja worker/scheduler e broker Redis.
- DAG nao atualiza:
  Verifique mount do diretorio `dags/` e logs do `dag-processor`.

## 8. Proximas melhorias (quando quiser evoluir)
1. Usar Airflow Connections em vez de credenciais no `.env`.
2. Criar testes automatizados para `transform` e `load`.
3. Adicionar validacoes de esquema antes do `to_sql`.
4. Trocar `to_sql` simples por estrategia de upsert/deduplicacao.

## 9. Evolucao aplicada: DW com dbt (raw/intermediate/mart)
Implementacao adotada neste projeto:
1. `load_data.py` cria schemas `raw`, `intermediate` e `mart`.
2. A carga bruta entra em `raw.weather_observations`.
3. O `upsert` incremental usa `ON CONFLICT (city_id, datetime)`.
4. Depois da carga RAW, a DAG executa `dbt run`.
5. O dbt materializa:
   - `intermediate.int_weather_observations` (incremental)
   - `mart.mart_weather_readings` (incremental)
   - `mart.mart_weather_daily_city` (view)
6. Em `intermediate` e `mart`, `data_observacao` fica em horário de Brasília (`America/Sao_Paulo`) sem offset, facilitando uso em dashboard.
7. Na `mart`, existe também `data_observacao_formatada` (`YYYY-MM-DD HH24:MI:SS`) para padronização visual.

Por que esse desenho e profissional:
- Separa ingestao de modelagem analitica.
- Permite reprocessamento controlado no dbt sem alterar RAW.
- Simplifica consumo no Power BI com camadas estaveis.

Guia dedicado do dbt neste projeto:
- `GUIA_DBT_WEATHER.md`
