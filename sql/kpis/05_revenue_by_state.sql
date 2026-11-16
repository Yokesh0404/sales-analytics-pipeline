-- =============================================================================
-- KPI 5: Revenue and orders by customer state
-- Business question: Where are our customers, and which regions are worth the most?
-- =============================================================================

with state_orders as (
    select
        c.state,
        o.order_id,
        o.order_total,
        c.customer_unique_id
    from analytics.fct_orders    as o
    join analytics.dim_customers as c on c.customer_id = o.customer_id
    where o.order_status = 'delivered'
)

select
    state,
    round(sum(order_total), 2)                                      as revenue,
    count(*)                                                        as orders,
    count(distinct customer_unique_id)                              as customers,
    round(sum(order_total) / count(*), 2)                           as aov,
    round(100.0 * sum(order_total) / sum(sum(order_total)) over (), 2) as revenue_share_pct
from state_orders
group by state
order by revenue desc;
