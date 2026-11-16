-- KPI table: one row per customer state. Sales, delivery and review KPIs together,
-- so the dashboard can draw one map/table per state. Delivered orders only.

with state_orders as (
    select
        c.state,
        c.customer_unique_id,
        o.order_total,
        o.is_late,
        o.delivery_days,
        o.review_score
    from {{ ref('fct_orders') }}    as o
    join {{ ref('dim_customers') }} as c on c.customer_id = o.customer_id
    where o.order_status = 'delivered'
)

select
    state,
    round(sum(order_total), 2)                                          as revenue,
    count(*)                                                            as orders,
    count(distinct customer_unique_id)                                  as customers,
    round(sum(order_total) / count(*), 2)                               as aov,
    round(100.0 * sum(order_total) / sum(sum(order_total)) over (), 2)  as revenue_share_pct,
    round(100.0 * avg(case when is_late then 1 else 0 end)
          filter (where is_late is not null), 1)                        as late_rate_pct,
    round(avg(delivery_days), 1)                                        as avg_delivery_days,
    round(avg(review_score), 2)                                         as avg_review_score
from state_orders
group by state
