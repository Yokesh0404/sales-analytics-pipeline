-- =============================================================================
-- KPI 8: Repeat customer rate
-- Business question: Do customers come back?
--
-- IMPORTANT: Olist gives a NEW customer_id to every order. The real person is
-- customer_unique_id, so we must count orders per customer_unique_id.
-- Repeat customer = a person with more than one delivered order.
-- =============================================================================

with orders_per_customer as (
    -- Step 1: how many orders, and how much revenue, per real person
    select
        c.customer_unique_id,
        count(*)           as orders,
        sum(o.order_total) as revenue
    from analytics.fct_orders    as o
    join analytics.dim_customers as c on c.customer_id = o.customer_id
    where o.order_status = 'delivered'
    group by c.customer_unique_id
)

-- Step 2: summarise into one row
select
    count(*)                                                     as customers,
    count(*) filter (where orders > 1)                           as repeat_customers,
    round(100.0 * count(*) filter (where orders > 1) / count(*), 2) as repeat_customer_rate_pct,
    round(100.0 * sum(revenue) filter (where orders > 1) / sum(revenue), 2) as repeat_revenue_share_pct,
    max(orders)                                                  as max_orders_by_one_customer
from orders_per_customer;
