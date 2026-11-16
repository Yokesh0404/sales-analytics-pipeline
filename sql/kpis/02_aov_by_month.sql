-- =============================================================================
-- KPI 2: Average order value (AOV) by month
-- Business question: Are customers spending more or less per order over time?
--
-- AOV = revenue / number of orders (delivered orders only).
-- =============================================================================

with order_values as (
    -- Step 1: one row per delivered order with its value and month
    select
        d.month_start    as month,
        o.order_id,
        o.order_total,   -- price + freight of all items in the order
        o.item_count
    from analytics.fct_orders as o
    join analytics.dim_date   as d on d.date_key = o.date_key
    where o.order_status = 'delivered'
)

-- Step 2: average per month
select
    month,
    count(*)                                  as orders,
    round(sum(order_total), 2)                as revenue,
    round(sum(order_total) / count(*), 2)     as aov,
    round(avg(item_count), 2)                 as avg_items_per_order
from order_values
group by month
order by month;
