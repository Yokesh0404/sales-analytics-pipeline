-- Singular test: returns a row (= FAIL) if the monthly KPI table doesn't add up
-- to the same delivered revenue as the fact table. Catches lost or duplicated rows.

with kpi as (
    select sum(revenue) as total from {{ ref('kpi_monthly_revenue') }}
),

fact as (
    select sum(item_total) as total
    from {{ ref('fct_order_items') }}
    where order_status = 'delivered'
)

select kpi.total as kpi_total, fact.total as fact_total
from kpi, fact
where abs(kpi.total - fact.total) > 1   -- allow for rounding each month to 2 decimals
