-- =============================================================================
-- KPI 6: On-time vs late delivery rate, and average delivery days, by state
-- Business question: Do we keep our delivery promises, and where do we fail?
--
-- Late    = delivered after the estimated delivery date shown at purchase.
-- Only orders with a delivery date are counted (8 'delivered' orders have none).
-- =============================================================================

with delivered as (
    select
        c.state,
        o.is_late,
        o.delivery_days,
        -- days past the promised date (only meaningful for late orders)
        o.delivered_at::date - o.estimated_delivery_at::date as days_late
    from analytics.fct_orders    as o
    join analytics.dim_customers as c on c.customer_id = o.customer_id
    where o.order_status = 'delivered'
      and o.delivered_at is not null
)

-- ROLLUP(state) adds one extra row with state = NULL that totals ALL states,
-- so we get the overall rate and the per-state rates from one query.
select
    coalesce(state, 'ALL')                                         as state,
    count(*)                                                       as delivered_orders,
    round(100.0 * avg(case when is_late then 0 else 1 end), 1)     as on_time_rate_pct,
    round(100.0 * avg(case when is_late then 1 else 0 end), 1)     as late_rate_pct,
    round(avg(delivery_days), 1)                                   as avg_delivery_days,
    round(avg(days_late) filter (where is_late), 1)                as avg_days_late_when_late
from delivered
group by rollup (state)
order by (state is null) desc, late_rate_pct desc;   -- 'ALL' first, then worst states
