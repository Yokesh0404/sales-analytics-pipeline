-- Dashboard cube: ORDER-level KPIs, one row per (month, customer state, main category,
-- delivery status). Each order is counted exactly once (via its main category),
-- and averages are stored as SUM + COUNT so they stay correct after filtering:
--     avg review = sum(review_score_sum) / sum(reviewed_orders)
-- Contains no customer-level data. Delivered orders only.

with orders as (
    select
        d.month_start                     as month,
        c.state                           as customer_state,
        coalesce(o.main_category, 'unknown') as main_category,
        o.order_total,
        o.delivery_days,
        o.review_score,
        case
            when o.delivered_at is null then '0. no delivery date'
            when not o.is_late then '1. on time'
            when o.delivered_at::date - o.estimated_delivery_at::date <= 3 then '2. late 1-3 days'
            when o.delivered_at::date - o.estimated_delivery_at::date <= 7 then '3. late 4-7 days'
            else '4. late 8+ days'
        end                               as delivery_status
    from {{ ref('fct_orders') }}    as o
    join {{ ref('dim_date') }}      as d on d.date_key = o.date_key
    join {{ ref('dim_customers') }} as c on c.customer_id = o.customer_id
    where o.order_status = 'delivered'
)

select
    month,
    customer_state,
    main_category,
    delivery_status,
    count(*)                                  as orders,
    round(sum(order_total), 2)                as order_revenue,
    coalesce(sum(delivery_days), 0)           as delivery_days_sum,
    count(delivery_days)                      as orders_with_delivery_date,
    count(review_score)                       as reviewed_orders,
    coalesce(sum(review_score), 0)            as review_score_sum,
    count(*) filter (where review_score = 1)  as one_star_reviews,
    count(*) filter (where review_score = 5)  as five_star_reviews
from orders
group by month, customer_state, main_category, delivery_status
