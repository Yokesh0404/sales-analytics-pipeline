-- Customer reviews.
-- Stage 3 found review_id is NOT unique: one review can be linked to several orders.
-- So the key here is (review_id, order_id), combined into review_key.
-- fct_orders later picks ONE review per order.

with source as (
    select * from {{ source('raw', 'order_reviews') }}
),

renamed as (
    select
        trim(review_id) || '-' || trim(order_id) as review_key,
        trim(review_id)                          as review_id,
        trim(order_id)                           as order_id,
        review_score::int                        as review_score,
        nullif(trim(review_comment_title), '')   as comment_title,    -- empty text -> NULL
        nullif(trim(review_comment_message), '') as comment_message,
        review_creation_date::timestamp          as review_created_at,
        review_answer_timestamp::timestamp       as review_answered_at
    from source
)

select distinct * from renamed
