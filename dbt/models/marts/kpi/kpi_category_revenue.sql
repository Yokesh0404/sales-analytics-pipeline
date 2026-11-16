-- KPI table: one row per product category (all categories, ranked). Delivered orders.

with category_revenue as (
    select
        p.category_name,
        sum(f.item_total)           as revenue,
        count(distinct f.order_id)  as orders,
        count(*)                    as items_sold
    from {{ ref('fct_order_items') }} as f
    join {{ ref('dim_products') }}    as p on p.product_id = f.product_id
    where f.order_status = 'delivered'
    group by p.category_name
)

select
    rank() over (order by revenue desc)                 as revenue_rank,
    category_name,
    round(revenue, 2)                                   as revenue,
    orders,
    items_sold,
    round(revenue / orders, 2)                          as avg_revenue_per_order,
    round(100.0 * revenue / sum(revenue) over (), 2)    as revenue_share_pct
from category_revenue
