"""Page 3: Customers & Delivery. States, delivery performance, reviews, repeat customers, cohorts."""
import plotly.express as px
import streamlit as st

from loaders import apply_filters, brl, insight, load

st.title("Customers & Delivery")

sales = apply_filters(load("kpi_sales_cube"))
orders = apply_filters(load("kpi_order_cube"), category_column="main_category")

if orders["orders"].sum() == 0:
    st.warning("No delivered orders match these filters. Try widening them.")
    st.stop()

left, right = st.columns(2)

# --- Revenue by state ----------------------------------------------------------------
with left:
    st.subheader("Revenue by customer state")
    by_state = sales.groupby("customer_state", as_index=False)["revenue"].sum().nlargest(15, "revenue")
    fig = px.bar(by_state.sort_values("revenue"), x="revenue", y="customer_state", orientation="h",
                 labels={"revenue": "Revenue (R$)", "customer_state": ""},
                 color_discrete_sequence=["#2E86AB"])
    fig.update_traces(hovertemplate="%{y}<br>R$ %{x:,.0f}<extra></extra>")
    fig.update_layout(height=450, margin=dict(t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    insight("**São Paulo is 37%** of revenue, and SP, RJ and MG together make up 63%. SP has the **lowest** AOV (R$ 142); "
            "remote northern states pay about R$ 220–245 per order, likely because of freight.")

# --- Late delivery rate by state --------------------------------------------------------
with right:
    st.subheader("Late delivery rate by customer state")
    delivered = orders[orders["delivery_status"] != "0. no delivery date"].copy()
    delivered["late_orders"] = delivered["orders"].where(delivered["delivery_status"] != "1. on time", 0)
    late = delivered.groupby("customer_state", as_index=False)[["orders", "late_orders"]].sum()
    late = late[late["orders"] >= 30]                      # skip tiny samples
    late["late_rate_pct"] = 100 * late["late_orders"] / late["orders"]
    overall = 100 * delivered["late_orders"].sum() / delivered["orders"].sum()
    fig = px.bar(late.nlargest(15, "late_rate_pct").sort_values("late_rate_pct"),
                 x="late_rate_pct", y="customer_state", orientation="h",
                 labels={"late_rate_pct": "Late orders (%)", "customer_state": ""},
                 color_discrete_sequence=["#C73E1D"], hover_data={"orders": ":,"})
    fig.add_vline(x=overall, line_dash="dash")
    fig.update_xaxes(title_text=f"Late orders (%) · dashed line = overall {overall:.1f}%")
    fig.update_layout(height=450, margin=dict(t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    insight("6.8% of orders arrive late overall, but the **northeast is 2–3× worse**: Alagoas 21%, Maranhão 17%. "
            "States with fewer than 30 delivered orders are hidden.")

# --- Review score vs delivery delay -----------------------------------------------------
st.subheader("Review score vs delivery delay")
reviews = (orders[orders["delivery_status"] != "0. no delivery date"]
           .groupby("delivery_status", as_index=False)
           [["reviewed_orders", "review_score_sum", "one_star_reviews"]].sum())
reviews["avg_review"] = reviews["review_score_sum"] / reviews["reviewed_orders"]
reviews["one_star_pct"] = 100 * reviews["one_star_reviews"] / reviews["reviewed_orders"]
reviews["status"] = reviews["delivery_status"].str[3:]     # drop the "1. " sort prefix

fig = px.bar(reviews, x="status", y="avg_review", text=reviews["avg_review"].map("{:.2f} ★".format),
             color="avg_review", color_continuous_scale="RdYlGn", range_color=(1, 5),
             labels={"status": "", "avg_review": "Avg review (1–5)"},
             hover_data={"reviewed_orders": ":,", "one_star_pct": ":.1f"})
fig.update_layout(height=380, coloraxis_showscale=False, yaxis_range=[0, 5], margin=dict(t=10, b=10))
st.plotly_chart(fig, width="stretch")
insight("**The strongest finding in the data.** On-time orders average **4.29 ★**. Just 1–3 days late drops it to 3.29, "
        "and 8+ days late to **1.70 ★, with 70% one-star reviews**. Fixing delivery is the biggest satisfaction lever.")

# --- Repeat customers + cohort retention ---------------------------------------------------
st.subheader("Do customers come back?")
st.caption("ℹ️ Customer-level metrics are calculated on the whole dataset. The state and category filters don't apply here; "
           "the month filter selects which cohorts are shown.")

repeat = load("kpi_repeat_customers").iloc[0]
m1, m2, m3 = st.columns(3)
m1.metric("Repeat customer rate", f"{repeat['repeat_customer_rate_pct']:.1f}%",
          help="Customers (customer_unique_id) with 2+ delivered orders")
m2.metric("Repeat customers", f"{int(repeat['repeat_customers']):,} of {int(repeat['customers']):,}")
m3.metric("Revenue from repeat customers", f"{repeat['repeat_revenue_share_pct']:.1f}%")

cohorts = apply_filters(load("kpi_cohort_retention"), month_column="cohort_month")
cohorts = cohorts[(cohorts["months_since_first"] >= 1) & (cohorts["months_since_first"] <= 12)]
if not cohorts.empty:
    heat = cohorts.pivot(index="cohort_month", columns="months_since_first", values="retention_pct")
    heat.index = heat.index.strftime("%b %Y")
    fig = px.imshow(heat, text_auto=".2f", aspect="auto", color_continuous_scale="Blues",
                    labels={"x": "Months after first purchase", "y": "First-purchase month (cohort)",
                            "color": "Retention %"})
    fig.update_layout(height=520, margin=dict(t=10, b=10))
    st.plotly_chart(fig, width="stretch")
insight("Only **3.0% of customers ever order twice**, and **under 0.5%** of any monthly cohort comes back in a later "
        "month. This didn't improve as Olist grew, so growth came almost entirely from new customers.")
