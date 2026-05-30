{{
    config(
        materialized ='table',
        alias ='daily_data'
    )
}}
select 
    ticker,
    SUM(volume) as volume,
    (array_agg(open ORDER BY timestamp ASC))[1] as open,
    (array_agg(close ORDER BY timestamp DESC ))[1] as close,
    MAX(high) as high,
    MIN(low) as low,
    SUM(no_txn) as total_txn,
    DATE(timestamp) as date_timestamp,
    NOW() as inserted_at
from  {{ref('staging')}}
group by ticker,date(timestamp)