-- Singular test: the dashboard cubes must add up to the same totals as the facts.
-- Returns rows (= FAIL) for any cube that loses or double-counts data.

with fact as (
    select
        (select sum(item_total) from {{ ref('fct_order_items') }} where order_status = 'delivered') as revenue,
        (select count(*)        from {{ ref('fct_orders') }}      where order_status = 'delivered') as orders
),

checks as (
    select 'kpi_sales_cube revenue'  as check_name, (select sum(revenue) from {{ ref('kpi_sales_cube') }})  as cube_value, revenue as fact_value from fact
    union all
    select 'kpi_order_cube orders',                 (select sum(orders) from {{ ref('kpi_order_cube') }}),               orders  from fact
    union all
    select 'kpi_order_cube revenue',                (select sum(order_revenue) from {{ ref('kpi_order_cube') }}),        revenue from fact
    union all
    select 'kpi_seller_cube revenue',               (select sum(revenue) from {{ ref('kpi_seller_cube') }}),             revenue from fact
)

select *
from checks
where abs(cube_value - fact_value) > 1   -- allow for rounding each cell to 2 decimals
