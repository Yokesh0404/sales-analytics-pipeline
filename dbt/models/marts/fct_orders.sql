-- Fact: one row per ORDER (grain = order).
-- Includes all orders, even the 775 with no items (mostly canceled/unavailable),
-- so status counts are complete. Money columns are 0 for those orders.

with orders as (
    select * from {{ ref('stg_orders') }}
),

-- Totals per order from its items.
items as (
    select
        order_id,
        count(*)           as item_count,
        sum(price)         as items_total,
        sum(freight_value) as freight_total
    from {{ ref('stg_order_items') }}
    group by order_id
),

-- Total paid per order (an order can have several payments).
payments as (
    select
        order_id,
        sum(payment_value) as payment_total
    from {{ ref('stg_order_payments') }}
    group by order_id
),

-- Some orders have more than one review: keep only the most recent one.
-- row_number() numbers each order's reviews 1, 2, 3 ... newest first.
reviews_ranked as (
    select
        order_id,
        review_score,
        row_number() over (
            partition by order_id
            order by review_created_at desc, review_answered_at desc, review_id
        ) as review_rank
    from {{ ref('stg_order_reviews') }}
)

select
    o.order_id,
    o.customer_id,
    to_char(o.purchased_at, 'YYYYMMDD')::int                      as date_key,
    o.order_status,
    o.purchased_at,
    o.delivered_to_customer_at                                     as delivered_at,
    o.estimated_delivery_at,
    coalesce(i.item_count, 0)                                      as item_count,
    coalesce(i.items_total, 0)                                     as items_total,
    coalesce(i.freight_total, 0)                                   as freight_total,
    coalesce(i.items_total, 0) + coalesce(i.freight_total, 0)      as order_total,
    p.payment_total,   -- NULL for the 1 order with no payment record
    -- Days from purchase to delivery. NULL if not delivered.
    o.delivered_to_customer_at::date - o.purchased_at::date        as delivery_days,
    -- Late = delivered after the promised date. NULL if not delivered.
    case
        when o.delivered_to_customer_at is null then null
        else o.delivered_to_customer_at::date > o.estimated_delivery_at::date
    end                                                            as is_late,
    r.review_score    -- NULL if the order has no review
from orders as o
left join items          as i on i.order_id = o.order_id
left join payments       as p on p.order_id = o.order_id
left join reviews_ranked as r on r.order_id = o.order_id and r.review_rank = 1
