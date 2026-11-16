-- =============================================================================
-- KPI 3: Top 10 product categories by revenue, with % share of total
-- Business question: Which categories drive the business?
-- =============================================================================

with category_revenue as (
    -- Step 1: revenue per category (delivered orders)
    select
        p.category_name,
        sum(f.item_total)           as revenue,
        count(distinct f.order_id)  as orders,
        count(*)                    as items_sold
    from analytics.fct_order_items as f
    join analytics.dim_products    as p on p.product_id = f.product_id
    where f.order_status = 'delivered'
    group by p.category_name
)

-- Step 2: share of total and rank.
-- sum(revenue) over () = the grand total, repeated on every row (a window function
-- with an empty window), so each row can be divided by it without a second query.
select
    rank() over (order by revenue desc)                       as revenue_rank,
    category_name,
    round(revenue, 2)                                         as revenue,
    orders,
    items_sold,
    round(100.0 * revenue / sum(revenue) over (), 2)          as revenue_share_pct
from category_revenue
order by revenue desc
limit 10;
