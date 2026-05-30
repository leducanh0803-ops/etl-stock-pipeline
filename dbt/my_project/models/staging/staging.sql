{{
    config(
        materialized='table',
        alias='stg_ohlcv'
    )
}}

with source as (
    select *,
    row_number() over(partition by ticker, ts order by ts) as rn
    from {{source('dev','raw_ohlcv_data')}}
),
de_dup as (
    select *
    from source
    where rn = 1
    and ticker is not null
    and close_price is not null
    and volume is not null
)
select 
    ticker,
    volume,
    open_price as open,
    close_price as close,
    high_price as high,
    low_price as low,
    ts as timestamp,
    no_txn,
    NOW() as inserted_at
from de_dup