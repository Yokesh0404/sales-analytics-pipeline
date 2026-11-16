-- One row per customer_id.
-- Note: Olist creates a NEW customer_id for every order. The real person is customer_unique_id.

with source as (
    select * from {{ source('raw', 'customers') }}
),

renamed as (
    select
        trim(customer_id)              as customer_id,
        trim(customer_unique_id)       as customer_unique_id,
        trim(customer_zip_code_prefix) as zip_code_prefix,   -- kept as text to keep leading zeros
        trim(customer_city)            as city,
        upper(trim(customer_state))    as state
    from source
)

-- "distinct" removes rows that are exact duplicates.
select distinct * from renamed
