-- One row per order, with clear names for each step of the order's life.

with source as (
    select * from {{ source('raw', 'orders') }}
),

renamed as (
    select
        trim(order_id)                               as order_id,
        trim(customer_id)                            as customer_id,
        lower(trim(order_status))                    as order_status,
        order_purchase_timestamp::timestamp          as purchased_at,
        order_approved_at::timestamp                 as approved_at,
        order_delivered_carrier_date::timestamp      as delivered_to_carrier_at,
        -- NULL for orders not delivered yet. Stage 3 also found 8 'delivered'
        -- orders with no date; they are left out of delivery KPIs automatically.
        order_delivered_customer_date::timestamp     as delivered_to_customer_at,
        order_estimated_delivery_date::timestamp     as estimated_delivery_at
    from source
)

select distinct * from renamed
