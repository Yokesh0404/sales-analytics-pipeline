-- Dimension: WHO bought. One row per customer_id.

select
    customer_id,
    customer_unique_id,   -- same person across orders -> use for repeat-customer analysis
    zip_code_prefix,
    city,
    state
from {{ ref('stg_customers') }}
