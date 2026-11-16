-- Dimension: WHAT was sold. One row per product.

select
    product_id,
    category_name,        -- English, or 'unknown'
    category_name_pt,     -- original Portuguese name
    name_length,
    description_length,
    photos_qty,
    weight_g,
    length_cm,
    height_cm,
    width_cm
from {{ ref('stg_products') }}
