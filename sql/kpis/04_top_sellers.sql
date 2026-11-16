-- =============================================================================
-- KPI 4: Top 10 sellers by revenue, with their average review score
-- Business question: Who are our most valuable sellers, and do customers like them?
--
-- Reviews belong to ORDERS, not items. If a seller has 3 items in one order,
-- that order's review must count once, so we first reduce to one row per
-- (seller, order) before averaging.
-- =============================================================================

with seller_orders as (
    -- Step 1: one row per seller per order
    select
        f.seller_id,
        f.order_id,
        sum(f.item_total)  as revenue,
        max(o.review_score) as review_score   -- same value on every item row of the order
    from analytics.fct_order_items as f
    join analytics.fct_orders      as o on o.order_id = f.order_id
    where f.order_status = 'delivered'
    group by f.seller_id, f.order_id
),

seller_summary as (
    -- Step 2: one row per seller
    select
        seller_id,
        sum(revenue)                   as revenue,
        count(*)                       as orders,
        round(avg(review_score), 2)    as avg_review_score,   -- avg() ignores orders with no review
        count(review_score)            as reviewed_orders
    from seller_orders
    group by seller_id
)

select
    rank() over (order by s.revenue desc) as revenue_rank,
    s.seller_id,
    d.state                               as seller_state,
    round(s.revenue, 2)                   as revenue,
    s.orders,
    s.avg_review_score,
    s.reviewed_orders
from seller_summary as s
join analytics.dim_sellers as d on d.seller_id = s.seller_id
order by s.revenue desc
limit 10;
