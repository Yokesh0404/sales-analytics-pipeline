-- Portuguese -> English category names.

with source as (
    select * from {{ source('raw', 'product_category_name_translation') }}
),

renamed as (
    select
        trim(product_category_name)         as category_name_pt,
        trim(product_category_name_english) as category_name_en
    from source
)

select distinct * from renamed
