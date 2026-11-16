-- Dimension: WHEN. One row per calendar day, covering every date in the orders data.
-- A date table lets us group by month/quarter/weekday without repeating date logic everywhere,
-- and it includes days with zero sales (useful for charts without gaps).

with bounds as (
    select
        min(purchased_at)::date as start_date,
        greatest(max(purchased_at), max(delivered_to_customer_at), max(estimated_delivery_at))::date as end_date
    from {{ ref('stg_orders') }}
),

days as (
    -- generate_series makes one row per day from start_date to end_date
    select generate_series(start_date, end_date, interval '1 day')::date as date_day
    from bounds
)

select
    to_char(date_day, 'YYYYMMDD')::int        as date_key,      -- e.g. 20180315
    date_day,
    extract(year from date_day)::int          as year,
    extract(quarter from date_day)::int       as quarter,
    extract(month from date_day)::int         as month,
    to_char(date_day, 'FMMonth')              as month_name,    -- FM removes padding spaces
    date_trunc('month', date_day)::date       as month_start,   -- handy for monthly charts
    extract(isodow from date_day)::int        as day_of_week,   -- 1 = Monday ... 7 = Sunday
    to_char(date_day, 'FMDay')                as day_name,
    extract(isodow from date_day) in (6, 7)   as is_weekend
from days
