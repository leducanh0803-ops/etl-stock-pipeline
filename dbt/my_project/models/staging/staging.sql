{{
    config(
        materialized='table',
        alias='stg_ohlcv'
    )
}}

with source as (
    select *,
    row_number() over(partition by ticker, date order by date) as rn
    from {{source('dev','ohlcv')}}
),
de_dup as (
    select *
    from source
    where rn = 1
    and ticker is not null
    and close is not null
    and volume is not null
)
select 
    date as timestamp,
    ticker,
    open,
    close,
    high,
    low,
    volume,
    weighted_volume,
    NOW () as inserted_at
from de_dup