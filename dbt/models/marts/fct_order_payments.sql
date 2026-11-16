-- Fact: one row per PAYMENT (grain = payment).
-- An order can be paid in several parts, e.g. a voucher + a credit card,
-- so payments get their own fact table instead of a column on fct_orders.

with payments as (
    select * from {{ ref('stg_order_payments') }}
),

orders as (
    select * from {{ ref('fct_orders') }}
)

select
    p.payment_key,
    p.order_id,
    o.customer_id,
    o.date_key,            -- purchase date of the order
    o.order_status,
    p.payment_sequential,  -- 1st, 2nd, ... payment on the order
    p.payment_type,
    p.payment_installments,
    p.payment_value
from payments as p
inner join orders as o on o.order_id = p.order_id
