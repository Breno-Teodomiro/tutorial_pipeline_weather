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

base as (
    select *
    from {{ ref('int_weather_observations') }}

    {% if is_incremental() %}
      where data_observacao > (select data_observacao_maxima from limite_incremental)
    {% endif %}
)

select
    chave_grao_clima,
    id_cidade,
    cidade,
    pais,
    data_observacao,
    to_char(data_observacao, 'YYYY-MM-DD HH24:MI:SS') as data_observacao_formatada,
    hora_observacao,
    data_referencia,
    hora_do_dia,
    clima_principal,
    descricao_clima,
    round(temperatura::numeric, 2) as temperatura_celsius,
    round(sensacao_termica::numeric, 2) as sensacao_termica_celsius,
    umidade,
    pressao,
    round(velocidade_vento::numeric, 2) as velocidade_vento,
    nebulosidade,
    visibilidade,
    latitude,
    longitude,
    data_carga_dw
from base
