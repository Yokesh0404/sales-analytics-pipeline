-- One row per item in an order. The natural key is (order_id, order_item_id);
-- we also build a single-column key so it is easy to test and join.

with source as (
    select * from {{ source('raw', 'order_items') }}
),

renamed as (
    select
        trim(order_id) || '-' || trim(order_item_id) as order_item_key,
        trim(order_id)                    as order_id,
        order_item_id::int                as order_item_id,   -- 1, 2, 3 ... within an order
        trim(product_id)                  as product_id,
        trim(seller_id)                   as seller_id,
        shipping_limit_date::timestamp    as shipping_limit_at,
        price::numeric(12, 2)             as price,
        freight_value::numeric(12, 2)     as freight_value
    from source
)

select distinct * from renamed
