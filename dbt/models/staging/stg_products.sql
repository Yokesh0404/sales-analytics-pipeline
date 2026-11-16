-- One row per product, with the category translated to English.
-- Fixes from Stage 3:
--   * 610 products have no category        -> 'unknown' (so their sales still count)
--   * 2 categories have no translation     -> translated by hand below

with products as (
    select * from {{ source('raw', 'products') }}
),

translation as (
    select * from {{ ref('stg_product_category_name_translation') }}
),

renamed as (
    select
        trim(p.product_id)                                  as product_id,
        coalesce(trim(p.product_category_name), 'unknown')  as category_name_pt,
        -- coalesce() returns the first value that is not NULL:
        -- official translation -> our manual translation -> 'unknown'
        coalesce(
            t.category_name_en,
            case trim(p.product_category_name)
                when 'pc_gamer' then 'pc_gamer'
                when 'portateis_cozinha_e_preparadores_de_alimentos'
                    then 'portable_kitchen_and_food_preparers'
            end,
            'unknown'
        )                                                   as category_name,
        -- the source columns are misspelled ("lenght"); we fix the names here
        p.product_name_lenght::numeric::int                 as name_length,
        p.product_description_lenght::numeric::int          as description_length,
        p.product_photos_qty::numeric::int                  as photos_qty,
        p.product_weight_g::numeric                         as weight_g,
        p.product_length_cm::numeric                        as length_cm,
        p.product_height_cm::numeric                        as height_cm,
        p.product_width_cm::numeric                         as width_cm
    from products as p
    left join translation as t
        on t.category_name_pt = trim(p.product_category_name)
)

select distinct * from renamed
