-- =============================================================================
-- KPI 1: Monthly revenue and order count, with month-over-month (MoM) growth
-- Business question: Is the business growing, and how fast?
--
-- Revenue = item price + freight, for DELIVERED orders, by purchase month.
-- Orders  = number of distinct delivered orders.
-- =============================================================================

with monthly as (
    -- Step 1: one row per month that has sales
    select
        d.month_start                as month,
        sum(f.item_total)            as revenue,
        count(distinct f.order_id)   as orders
    from analytics.fct_order_items as f
    join analytics.dim_date        as d on d.date_key = f.date_key
    where f.order_status = 'delivered'
    group by d.month_start
),

month_spine as (
    -- Step 2: every month between the first and last sale, so a month with
    -- zero sales still appears (otherwise LAG would compare with the wrong month)
    select distinct d.month_start as month
    from analytics.dim_date as d
    where d.month_start between (select min(month) from monthly)
                            and (select max(month) from monthly)
),

filled as (
    select
        s.month,
        coalesce(m.revenue, 0) as revenue,
        coalesce(m.orders, 0)  as orders
    from month_spine as s
    left join monthly as m on m.month = s.month
)

-- Step 3: LAG() looks at the previous row (= previous month) so we can compare
select
    month,
    revenue,
    orders,
    lag(revenue) over (order by month) as prev_month_revenue,
    round(100.0 * (revenue - lag(revenue) over (order by month))
          / nullif(lag(revenue) over (order by month), 0), 1) as revenue_mom_growth_pct,
    round(100.0 * (orders - lag(orders) over (order by month))
          / nullif(lag(orders) over (order by month), 0), 1)  as orders_mom_growth_pct
from filled
order by month;
