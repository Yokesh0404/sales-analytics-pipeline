-- KPI table: one row per payment type. All payments (any order status).

select
    payment_type,
    count(*)                                                                as payments,
    round(100.0 * count(*) / sum(count(*)) over (), 2)                      as count_share_pct,
    round(sum(payment_value), 2)                                            as payment_value,
    round(100.0 * sum(payment_value) / sum(sum(payment_value)) over (), 2)  as value_share_pct,
    round(avg(payment_value), 2)                                            as avg_payment_value,
    round(avg(payment_installments), 1)                                     as avg_installments
from {{ ref('fct_order_payments') }}
group by payment_type
