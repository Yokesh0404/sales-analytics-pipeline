-- KPI table: one row per (cohort month, months since first purchase).
-- Cohort = customers whose first delivered order was in the same month.

with customer_months as (
    select distinct
        c.customer_unique_id,
        date_trunc('month', o.purchased_at)::date as order_month
    from {{ ref('fct_orders') }}    as o
    join {{ ref('dim_customers') }} as c on c.customer_id = o.customer_id
    where o.order_status = 'delivered'
),

first_purchase as (
    select customer_unique_id, min(order_month) as cohort_month
    from customer_months
    group by customer_unique_id
),

cohort_size as (
    select cohort_month, count(*) as cohort_customers
    from first_purchase
    group by cohort_month
),

activity as (
    select
        f.cohort_month,
        ((extract(year from m.order_month) - extract(year from f.cohort_month)) * 12
          + (extract(month from m.order_month) - extract(month from f.cohort_month)))::int as months_since_first
    from customer_months as m
    join first_purchase  as f on f.customer_unique_id = m.customer_unique_id
)

select
    a.cohort_month,
    a.months_since_first,
    s.cohort_customers,
    count(*)                                          as active_customers,
    round(100.0 * count(*) / s.cohort_customers, 2)   as retention_pct
from activity as a
join cohort_size as s on s.cohort_month = a.cohort_month
group by a.cohort_month, a.months_since_first, s.cohort_customers
