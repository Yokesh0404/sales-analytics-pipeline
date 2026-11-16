-- =============================================================================
-- KPI 10: Monthly cohort retention
-- Business question: Of the customers who first bought in month X, how many
--                    bought again 1, 2, 3 ... months later?
--
-- Cohort           = all customers whose FIRST delivered order was in the same month.
-- months_since_first = 0 for the first month, 1 for the next month, and so on.
-- retention_pct    = % of the cohort that ordered in that month.
-- =============================================================================

with customer_months as (
    -- Step 1: every month in which each real person placed a delivered order
    select distinct
        c.customer_unique_id,
        date_trunc('month', o.purchased_at)::date as order_month
    from analytics.fct_orders    as o
    join analytics.dim_customers as c on c.customer_id = o.customer_id
    where o.order_status = 'delivered'
),

first_purchase as (
    -- Step 2: each person's cohort = the month of their first order
    select
        customer_unique_id,
        min(order_month) as cohort_month
    from customer_months
    group by customer_unique_id
),

cohort_size as (
    -- Step 3: how many people are in each cohort
    select cohort_month, count(*) as cohort_customers
    from first_purchase
    group by cohort_month
),

activity as (
    -- Step 4: for every order month, how many months after the cohort month is it?
    select
        f.cohort_month,
        (extract(year from m.order_month) - extract(year from f.cohort_month)) * 12
          + (extract(month from m.order_month) - extract(month from f.cohort_month)) as months_since_first,
        m.customer_unique_id
    from customer_months as m
    join first_purchase  as f on f.customer_unique_id = m.customer_unique_id
)

-- Step 5: count active people per cohort per month, as a % of the cohort
select
    a.cohort_month,
    a.months_since_first::int                                         as months_since_first,
    s.cohort_customers,
    count(*)                                                          as active_customers,
    round(100.0 * count(*) / s.cohort_customers, 2)                   as retention_pct
from activity as a
join cohort_size as s on s.cohort_month = a.cohort_month
group by a.cohort_month, a.months_since_first, s.cohort_customers
order by a.cohort_month, months_since_first;
