-- One row per payment on an order (an order can be paid with several methods).
-- The natural key is (order_id, payment_sequential).

with source as (
    select * from {{ source('raw', 'order_payments') }}
),

renamed as (
    select
        trim(order_id) || '-' || trim(payment_sequential) as payment_key,
        trim(order_id)                     as order_id,
        payment_sequential::int            as payment_sequential,
        lower(trim(payment_type))          as payment_type,
        payment_installments::int          as payment_installments,
        payment_value::numeric(12, 2)      as payment_value
    from source
)

select distinct * from renamed
