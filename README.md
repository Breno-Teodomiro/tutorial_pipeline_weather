# Tutorial Pipeline Weather

---

Pipeline simples de dados climáticos com foco em prática de ETL em Python.

O projeto atualmente possui duas etapas implementadas:
- `extract`: consulta a API da OpenWeather e salva JSON local.
- `transform`: normaliza e prepara os dados em `pandas.DataFrame`.

## Stack
- Python `>=3.12`
- `requests`
- `pandas`
- `python-dotenv` (dependência instalada, ainda não integrada no código)
- `SQLAlchemy` e `psycopg2-binary` (dependências instaladas, etapa de load ainda não implementada)

## Estrutura do projeto
```text
.
├── config/
│   └── .env
├── data/
│   └── weather_data.json
├── noteboooks/
│   └── anlysis_data.ipynb
├── src/
│   ├── extract_data.py
│   └── transform_data.py
├── pyproject.toml
└── README.md
```

## Como preparar ambiente

### Opção 1: usando `uv` (recomendado neste projeto)
```bash
uv sync
```

### Opção 2: usando `venv` + `pip`
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Como executar

### 1) Extração
Executa a chamada da API e grava em `data/weather_data.json`.

```bash
python -c "from src.extract_data import extract_weather_data, url; extract_weather_data(url)"
```

### 2) Transformação
Executa as transformações e retorna um `DataFrame`.

```bash
python -c "from src.transform_data import data_transformations; print(data_transformations().head())"
```

## Diagnóstico rápido do estado atual
Durante a análise do projeto, foram identificados pontos importantes:

1. `README.md` estava vazio.
2. `src/transform_data.py` tem erro de digitação em `path.existis()` (correto: `path.exists()`), o que interrompe a transformação.
3. A API key está hardcoded em `src/extract_data.py`, e o `.env` ainda não é usado no fluxo.
4. Não há etapa de `load` implementada, apesar de já existirem dependências de banco.
5. Não existem testes automatizados no repositório.

## Próximos passos recomendados
1. Corrigir `path.existis()` para `path.exists()`.
2. Mover a API key para variável de ambiente (`config/.env`) e ler via `python-dotenv`.
3. Adicionar função `main`/CLI para execução direta de cada etapa.
4. Implementar etapa de `load` (ex.: PostgreSQL via `SQLAlchemy`).
5. Criar testes para extração e transformação.

---