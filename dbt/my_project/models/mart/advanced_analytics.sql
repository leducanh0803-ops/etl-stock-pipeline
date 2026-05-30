{{
    config(
        materialized ='table',
        alias ='advanced_analytics'
    )
}}

with daily as (
    select * from {{ ref('ohlcv_daily') }}
),
price_changes as (
    select
        ticker,
        date_timestamp,
        close,
        close - LAG(close) OVER (
            PARTITION BY ticker ORDER BY date_timestamp
        ) as price_change
    from daily
),
gains_losses as (
    select
        ticker,
        date_timestamp,
        CASE WHEN price_change > 0 THEN price_change ELSE 0 END as gain,
        CASE WHEN price_change < 0 THEN ABS(price_change) ELSE 0 END as loss
    from price_changes 
),
avg_gl as (
    select 
        ticker,
        date_timestamp,
        avg(gain) over(
            partition by ticker
            order by date_timestamp
            rows between 13 preceding and current row
        ) as avg_gain,
        avg(loss) over(
            partition by ticker
            order by date_timestamp
            rows between 13 preceding and current row
        ) as avg_loss
    from gains_losses

)
select
    d.ticker,
    d.date_timestamp,
    d.close,
    AVG(d.close) OVER(
        PARTITION BY d.ticker
        ORDER BY d.date_timestamp
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as ma7,
    avg(close) over(
        PARTITION BY d.ticker
        ORDER BY d.date_timestamp
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
   ) as ma20,
   (avg(d.close) over(
        PARTITION BY d.ticker
        ORDER BY d.date_timestamp
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
   ) + 
   (2* STDDEV(d.close) over (
        partition by d.ticker
        order by d.date_timestamp
        rows between 19 preceding and current row
   ))) as upper_band,
   (avg(d.close) over(
        PARTITION BY d.ticker
        ORDER BY d.date_timestamp
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
   )- 
   (2* STDDEV(d.close) over (
        partition by d.ticker
        order by d.date_timestamp
        rows between 19 preceding and current row
   ))) as lower_band,
   100 -100/(1+gl.avg_gain/NULLIF(gl.avg_loss,0)) as rsi
from daily d
join avg_gl gl
on
    d.date_timestamp = gl.date_timestamp
    and d.ticker = gl.ticker