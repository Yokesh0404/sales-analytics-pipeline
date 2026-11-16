-- Singular test: returns rows (= FAIL) if the cohort table breaks its own rules:
--   * month 0 must be 100% (everyone buys in their first month, by definition)
--   * (cohort_month, months_since_first) must be unique
--   * retention can't be negative or above 100%

select cohort_month, months_since_first, 'month 0 is not 100%' as problem
from {{ ref('kpi_cohort_retention') }}
where months_since_first = 0 and retention_pct <> 100

union all

select cohort_month, months_since_first, 'duplicate row' as problem
from {{ ref('kpi_cohort_retention') }}
group by cohort_month, months_since_first
having count(*) > 1

union all

select cohort_month, months_since_first, 'retention out of range' as problem
from {{ ref('kpi_cohort_retention') }}
where retention_pct < 0 or retention_pct > 100 or months_since_first < 0
