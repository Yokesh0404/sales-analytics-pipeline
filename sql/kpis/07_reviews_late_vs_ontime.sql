-- =============================================================================
-- KPI 7: Average review score, late vs on-time orders
-- Business question: How much does late delivery hurt customer satisfaction?
--
-- Late orders are split into buckets to see if "a little late" differs from
-- "very late".
-- =============================================================================

with reviewed as (
    select
        o.review_score,
        case
            when not o.is_late then '1. on time'
            when o.delivered_at::date - o.estimated_delivery_at::date <= 3 then '2. late 1-3 days'
            when o.delivered_at::date - o.estimated_delivery_at::date <= 7 then '3. late 4-7 days'
            else '4. late 8+ days'
        end as delivery_status
    from analytics.fct_orders as o
    where o.order_status = 'delivered'
      and o.delivered_at is not null
      and o.review_score is not null
)

select
    delivery_status,
    count(*)                                                       as reviewed_orders,
    round(avg(review_score), 2)                                    as avg_review_score,
    round(100.0 * avg(case when review_score = 1 then 1 else 0 end), 1) as one_star_pct,
    round(100.0 * avg(case when review_score = 5 then 1 else 0 end), 1) as five_star_pct
from reviewed
group by delivery_status
order by delivery_status;
