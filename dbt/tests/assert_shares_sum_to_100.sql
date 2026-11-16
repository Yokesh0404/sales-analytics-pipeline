-- Singular test: % shares must add up to 100 (within rounding). Returns rows (= FAIL) if not.

select 'kpi_category_revenue' as model, sum(revenue_share_pct) as total_pct
from {{ ref('kpi_category_revenue') }}
having abs(sum(revenue_share_pct) - 100) > 0.5

union all

select 'kpi_state_summary', sum(revenue_share_pct)
from {{ ref('kpi_state_summary') }}
having abs(sum(revenue_share_pct) - 100) > 0.5

union all

select 'kpi_payment_mix', sum(value_share_pct)
from {{ ref('kpi_payment_mix') }}
having abs(sum(value_share_pct) - 100) > 0.5
