-- =============================================================================
-- KPI 9: Payment type mix (count and value share)
-- Business question: How do customers pay, and how much do they use installments?
--
-- Uses ALL payments (any order status): this KPI is about payment behaviour,
-- not delivered revenue.
-- =============================================================================

select
    payment_type,
    count(*)                                                       as payments,
    round(100.0 * count(*) / sum(count(*)) over (), 2)             as count_share_pct,
    round(sum(payment_value), 2)                                   as payment_value,
    round(100.0 * sum(payment_value) / sum(sum(payment_value)) over (), 2) as value_share_pct,
    round(avg(payment_value), 2)                                   as avg_payment_value,
    round(avg(payment_installments), 1)                            as avg_installments
from analytics.fct_order_payments
group by payment_type
order by payment_value desc;
