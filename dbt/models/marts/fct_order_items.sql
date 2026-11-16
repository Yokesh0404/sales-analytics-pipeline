-- Fact: one row per ORDER ITEM (grain = order item).
-- This is the finest level that links to one product and one seller,
-- so it's the table for revenue by category / product / seller.
-- Order-level values (customer, date, delivery) come from fct_orders.

with items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('fct_orders') }}
)

select
    i.order_item_key,
    i.order_id,
    i.order_item_id,
    i.product_id,
    i.seller_id,
    o.customer_id,
    o.date_key,
    o.order_status,
    i.price,
    i.freight_value,
    i.price + i.freight_value                                       as item_total,
    -- Payments are recorded per ORDER, not per item. To give each item a fair part,
    -- split the order's payment in proportion to the item's share of the order value.
    -- nullif(..., 0) avoids dividing by zero.
    round(o.payment_total * (i.price + i.freight_value) / nullif(o.order_total, 0), 2)
                                                                    as payment_value_share,
    o.delivery_days,
    o.is_late
from items as i
inner join orders as o on o.order_id = i.order_id
