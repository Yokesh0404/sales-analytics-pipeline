-- Dashboard cube: seller performance, one row per (seller, month, customer state, category).
-- Revenue is exact per item category. Order-level values (orders, reviews) use the
-- category with the most revenue in that seller's part of the order, so each
-- seller-order is counted once. seller_id is a business ID, not personal data.
-- Delivered orders only.

with seller_items as (
    select
        f.seller_id,
        f.order_id,
        d.month_start   as month,
        c.state         as customer_state,
        p.category_name,
        f.item_total
    from {{ ref('fct_order_items') }} as f
    join {{ ref('dim_date') }}        as d on d.date_key = f.date_key
    join {{ ref('dim_customers') }}   as c on c.customer_id = f.customer_id
    join {{ ref('dim_products') }}    as p on p.product_id = f.product_id
    where f.order_status = 'delivered'
),

-- one row per (seller, order, category) with that category's revenue
seller_order_category as (
    select
        seller_id, order_id, month, customer_state, category_name,
        sum(item_total) as revenue,
        count(*)        as items_sold,
        row_number() over (
            partition by seller_id, order_id
            order by sum(item_total) desc, category_name
        ) as category_rank   -- 1 = this seller's main category in the order
    from seller_items
    group by seller_id, order_id, month, customer_state, category_name
)

select
    s.seller_id,
    ds.state                                                       as seller_state,
    s.month,
    s.customer_state,
    s.category_name,
    round(sum(s.revenue), 2)                                       as revenue,
    sum(s.items_sold)                                              as items_sold,
    count(*) filter (where s.category_rank = 1)                    as orders,
    count(o.review_score) filter (where s.category_rank = 1)       as reviewed_orders,
    coalesce(sum(o.review_score) filter (where s.category_rank = 1), 0) as review_score_sum
from seller_order_category as s
join {{ ref('fct_orders') }}  as o  on o.order_id = s.order_id
join {{ ref('dim_sellers') }} as ds on ds.seller_id = s.seller_id
group by s.seller_id, ds.state, s.month, s.customer_state, s.category_name
