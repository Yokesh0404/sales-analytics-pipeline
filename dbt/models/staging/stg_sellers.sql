-- One row per seller.

with source as (
    select * from {{ source('raw', 'sellers') }}
),

renamed as (
    select
        trim(seller_id)              as seller_id,
        trim(seller_zip_code_prefix) as zip_code_prefix,
        trim(seller_city)            as city,
        upper(trim(seller_state))    as state
    from source
)

select distinct * from renamed
