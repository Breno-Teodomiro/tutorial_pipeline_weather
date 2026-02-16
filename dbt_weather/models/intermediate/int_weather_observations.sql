{{
  config(
    materialized='incremental',
    unique_key='chave_grao_clima',
    on_schema_change='sync_all_columns'
  )
}}

with limite_incremental as (
    {% if is_incremental() %}
    select
        coalesce(max(data_observacao), '1900-01-01'::timestamp) as data_observacao_maxima
    from {{ this }}
    {% else %}
    select '1900-01-01'::timestamp as data_observacao_maxima
    {% endif %}
),

src as (
    select *
    from {{ ref('stg_weather_observations') }}

    {% if is_incremental() %}
      where timezone('America/Sao_Paulo', data_observacao) > (select data_observacao_maxima from limite_incremental)
    {% endif %}
)

, src_brasil as (
    select
        *,
        date_trunc('second', timezone('America/Sao_Paulo', data_observacao)) as data_observacao_brasil
    from src
)

select
    md5(id_cidade::text || '-' || data_observacao_brasil::text) as chave_grao_clima,
    id_cidade,
    cidade,
    pais,
    data_observacao_brasil as data_observacao,
    date_trunc('hour', data_observacao_brasil) as hora_observacao,
    date_trunc('day', data_observacao_brasil) as data_referencia,
    extract(hour from data_observacao_brasil) as hora_do_dia,
    id_clima,
    clima_principal,
    descricao_clima,
    temperatura,
    sensacao_termica,
    temperatura_minima,
    temperatura_maxima,
    pressao,
    umidade,
    nivel_mar,
    nivel_solo,
    velocidade_vento,
    direcao_vento,
    rajada_vento,
    nebulosidade,
    visibilidade,
    longitude,
    latitude,
    data_ingestao,
    now() as data_carga_dw
from src_brasil
