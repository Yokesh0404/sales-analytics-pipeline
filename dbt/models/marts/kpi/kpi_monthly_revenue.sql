-- KPI table: one row per month. Revenue, orders, AOV and month-over-month growth.
-- Same logic as sql/kpis/01 and 02. Revenue = price + freight of DELIVERED orders.

with monthly as (
    select
        d.month_start               as month,
        sum(f.item_total)           as revenue,
        count(distinct f.order_id)  as orders
    from {{ ref('fct_order_items') }} as f
    join {{ ref('dim_date') }}        as d on d.date_key = f.date_key
    where f.order_status = 'delivered'
    group by d.month_start
),

-- every month between first and last sale, so empty months show as 0
month_spine as (
    select distinct d.month_start as month
    from {{ ref('dim_date') }} as d
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

select
    month,
    round(revenue, 2)                                   as revenue,
    orders,
    round(revenue / nullif(orders, 0), 2)               as aov,
    round(100.0 * (revenue - lag(revenue) over (order by month))
          / nullif(lag(revenue) over (order by month), 0), 1) as revenue_mom_growth_pct,
    round(100.0 * (orders - lag(orders) over (order by month))
          / nullif(lag(orders) over (order by month), 0), 1)  as orders_mom_growth_pct
from filled
