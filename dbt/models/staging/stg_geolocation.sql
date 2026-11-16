-- Zip code prefix -> latitude/longitude. The raw table has ~262k exact duplicate rows,
-- which "distinct" removes. A zip prefix can still have several coordinates, so there is no unique key.

with source as (
    select * from {{ source('raw', 'geolocation') }}
),

renamed as (
    select
        trim(geolocation_zip_code_prefix) as zip_code_prefix,
        geolocation_lat::numeric          as latitude,
        geolocation_lng::numeric          as longitude,
        trim(geolocation_city)            as city,
        upper(trim(geolocation_state))    as state
    from source
)

select distinct * from renamed
