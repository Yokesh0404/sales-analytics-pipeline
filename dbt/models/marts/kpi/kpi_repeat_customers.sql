-- KPI table: a single row with the repeat-customer KPIs.
-- Counts per customer_unique_id (the real person), not customer_id (new per order).

with orders_per_customer as (
    select
        c.customer_unique_id,
        count(*)           as orders,
        sum(o.order_total) as revenue
    from {{ ref('fct_orders') }}    as o
    join {{ ref('dim_customers') }} as c on c.customer_id = o.customer_id
    where o.order_status = 'delivered'
    group by c.customer_unique_id
)

select
    count(*)                                                                as customers,
    count(*) filter (where orders > 1)                                      as repeat_customers,
    round(100.0 * count(*) filter (where orders > 1) / count(*), 2)         as repeat_customer_rate_pct,
    round(100.0 * sum(revenue) filter (where orders > 1) / sum(revenue), 2) as repeat_revenue_share_pct,
    round(avg(orders), 3)                                                   as avg_orders_per_customer,
    max(orders)                                                             as max_orders_by_one_customer
from orders_per_customer
