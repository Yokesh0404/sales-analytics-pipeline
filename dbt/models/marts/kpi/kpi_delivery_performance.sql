-- KPI table: one row per purchase month. Delivery speed, late rate, and how
-- review scores differ for on-time vs late orders. Delivered orders with a delivery date.

with delivered as (
    select
        d.month_start as month,
        o.is_late,
        o.delivery_days,
        o.review_score
    from {{ ref('fct_orders') }} as o
    join {{ ref('dim_date') }}   as d on d.date_key = o.date_key
    where o.order_status = 'delivered'
      and o.delivered_at is not null
)

select
    month,
    count(*)                                                   as delivered_orders,
    count(*) filter (where is_late)                            as late_orders,
    round(100.0 * avg(case when is_late then 1 else 0 end), 1) as late_rate_pct,
    round(avg(delivery_days), 1)                               as avg_delivery_days,
    round(avg(review_score) filter (where not is_late), 2)     as avg_review_on_time,
    round(avg(review_score) filter (where is_late), 2)         as avg_review_late
from delivered
group by month
