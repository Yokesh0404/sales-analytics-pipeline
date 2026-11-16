# KPI Definitions: Olist Sales Analytics

Each KPI below says **what** it measures, **how** it's calculated, **which business question** it answers, and **where** to find it. All KPIs read only the `analytics` schema (the star schema built by dbt).

## Common rules

These apply to every KPI unless the KPI says otherwise.

| Term | Definition |
|---|---|
| **Revenue** | Item `price` + `freight_value`, in Brazilian reais (BRL), for orders with status `delivered`. Canceled, unavailable and in-progress orders are excluded. |
| **Order** | One distinct `order_id` with status `delivered`. |
| **Month** | The month the customer **placed** the order (`purchased_at`), not the delivery month. |
| **Customer** | A real person = `customer_unique_id`. Olist issues a new `customer_id` for every order, so `customer_id` can't be used to count people. |
| **Late** | Delivered to the customer after the estimated delivery date shown at purchase (compared by calendar day). |
| **Data range** | Delivered orders run from Sep 2016 to Aug 2018. 2016 has very few orders (and none in Nov 2016), so trend analysis should start from Jan 2017. |

## KPIs

| # | KPI | Definition | Formula | Business question | SQL file / dbt table |
|---|---|---|---|---|---|
| 1 | **Monthly revenue & orders, MoM growth** | Revenue and delivered orders per purchase month, with % change vs the previous month | `revenue = SUM(price + freight)`; `MoM % = (this month − last month) / last month × 100` (`LAG`) | Is the business growing, and how fast? | `sql/kpis/01_monthly_revenue.sql` · `kpi_monthly_revenue` |
| 2 | **Average order value (AOV)** | Average revenue per delivered order, by month | `AOV = revenue / orders` | Are customers spending more or less per order? | `02_aov_by_month.sql` · `kpi_monthly_revenue.aov` |
| 3 | **Top categories & revenue share** | Revenue per product category and its % of total revenue | `share % = category revenue / SUM(all revenue) × 100` | Which categories drive the business? | `03_top_categories.sql` · `kpi_category_revenue` |
| 4 | **Top sellers & review score** | Revenue per seller, plus the average review score of the seller's orders (each order counted once) | `avg review = AVG(review_score)` over the seller's distinct orders | Who are the most valuable sellers, and do customers like them? | `04_top_sellers.sql` · `kpi_seller_performance` |
| 5 | **Revenue & orders by state** | Revenue, orders, customers and AOV per customer state | `share % = state revenue / total × 100` | Where are our customers, and which regions are worth most? | `05_revenue_by_state.sql` · `kpi_state_summary` |
| 6 | **On-time vs late delivery rate** | % of delivered orders that arrived on or before the promised date; average delivery days; overall and by state | `late rate % = late orders / delivered orders × 100`; `delivery days = delivered date − purchase date` | Do we keep our delivery promises, and where do we fail? | `06_delivery_performance.sql` · `kpi_state_summary`, `kpi_delivery_performance` |
| 7 | **Review score: late vs on-time** | Average review score and % of 1-star / 5-star reviews, for on-time orders and for late orders grouped by days late | `AVG(review_score)` grouped by delivery status | How much does late delivery hurt satisfaction? | `07_reviews_late_vs_ontime.sql` · `kpi_delivery_performance` (on-time vs late per month) |
| 8 | **Repeat customer rate** | % of real customers with more than one delivered order, and their share of revenue | `repeat rate % = customers with 2+ orders / all customers × 100` | Do customers come back? | `08_repeat_customers.sql` · `kpi_repeat_customers` |
| 9 | **Payment type mix** | Number and value of payments per payment type, plus average installments. Uses **all** payments, because it measures payment behaviour, not revenue. | `value share % = type value / total value × 100` | How do customers pay? | `09_payment_mix.sql` · `kpi_payment_mix` |
| 10 | **Monthly cohort retention** | Customers grouped by the month of their first order (cohort). For each later month, the % of the cohort that ordered again. | `retention % = active customers in month N / cohort size × 100` | Do new customers become loyal customers? | `10_cohort_retention.sql` · `kpi_cohort_retention` |

## Key results (data as of the 2026-11-16 pipeline run)

| KPI | Headline number |
|---|---|
| Total delivered revenue | R$ 15.42M from 96,478 orders (Sep 2016 – Aug 2018) |
| Monthly revenue, 2018 | Flat at about R$ 1.0–1.13M per month (Jan–Aug 2018) |
| Peak month | Nov 2017: R$ 1.15M, +53.6% vs Oct (Black Friday) |
| AOV | About R$ 150–170, stable over time |
| Top category | `health_beauty`: 9.2% of revenue. The top 10 categories are 62.4% of revenue. |
| Top state | São Paulo (SP): 37.4% of revenue, but the lowest AOV (R$ 142) |
| Late delivery rate | 6.8% overall; worst in Alagoas (AL) at 21.4% |
| Review score | 4.29 on time → 1.70 when 8+ days late |
| Repeat customer rate | 3.0% of customers, 5.6% of revenue |
| Payment mix | Credit card: 74% of payments, 78% of value, 3.5 installments on average |
| Retention | Below 0.5% of a cohort orders again in any later month |

## Tests that protect these numbers

- Every KPI table has `unique` and `not_null` tests on its key (month, category, seller, state, payment type).
- `assert_kpi_revenue_matches_facts`: the monthly KPI table must add up to the same revenue as `fct_order_items`.
- `assert_shares_sum_to_100`: category, state and payment shares must each total 100% (within rounding).
- `assert_cohort_retention_valid`: month 0 is always 100%, there are no duplicate cohort rows, and retention is between 0 and 100%.
