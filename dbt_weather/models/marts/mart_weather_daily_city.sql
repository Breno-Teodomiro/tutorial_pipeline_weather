{{ config(materialized='view') }}

select
    id_cidade,
    cidade,
    pais,
    data_referencia,
    avg(temperatura) as media_temperatura,
    min(temperatura_minima) as temperatura_minima_dia,
    max(temperatura_maxima) as temperatura_maxima_dia,
    avg(umidade) as media_umidade,
    avg(velocidade_vento) as media_velocidade_vento,
    count(*) as quantidade_leituras
from {{ ref('int_weather_observations') }}
group by 1,2,3,4
