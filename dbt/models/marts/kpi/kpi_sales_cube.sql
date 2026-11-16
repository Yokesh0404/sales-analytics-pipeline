-- Dashboard cube: ITEM-level revenue, one row per (month, customer state, category).
-- Every column can be ADDED UP, so the dashboard can apply any combination of
-- date / state / category filters and just sum the matching rows.
-- Contains no customer-level data. Delivered orders only.

select
    d.month_start               as month,
    c.state                     as customer_state,
    p.category_name,
    round(sum(f.price), 2)          as item_revenue,
    round(sum(f.freight_value), 2)  as freight_revenue,
    round(sum(f.item_total), 2)     as revenue,       -- price + freight
    count(*)                        as items_sold
from {{ ref('fct_order_items') }} as f
join {{ ref('dim_date') }}        as d on d.date_key = f.date_key
join {{ ref('dim_customers') }}   as c on c.customer_id = f.customer_id
join {{ ref('dim_products') }}    as p on p.product_id = f.product_id
where f.order_status = 'delivered'
group by d.month_start, c.state, p.category_name
