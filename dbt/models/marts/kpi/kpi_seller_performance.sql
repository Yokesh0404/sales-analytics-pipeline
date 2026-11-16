-- KPI table: one row per seller. Revenue, orders, average review, late rate. Delivered orders.
-- Reviews and lateness are per ORDER, so we first reduce to one row per (seller, order).

with seller_orders as (
    select
        f.seller_id,
        f.order_id,
        sum(f.item_total)    as revenue,
        max(o.review_score)  as review_score,
        bool_or(o.is_late)   as is_late
    from {{ ref('fct_order_items') }} as f
    join {{ ref('fct_orders') }}      as o on o.order_id = f.order_id
    where f.order_status = 'delivered'
    group by f.seller_id, f.order_id
)

select
    so.seller_id,
    s.state                                                   as seller_state,
    round(sum(so.revenue), 2)                                 as revenue,
    count(*)                                                  as orders,
    round(avg(so.review_score), 2)                            as avg_review_score,
    count(so.review_score)                                    as reviewed_orders,
    round(100.0 * avg(case when so.is_late then 1 else 0 end)
          filter (where so.is_late is not null), 1)           as late_rate_pct,
    rank() over (order by sum(so.revenue) desc)               as revenue_rank
from seller_orders as so
join {{ ref('dim_sellers') }} as s on s.seller_id = so.seller_id
group by so.seller_id, s.state
