"""Page 1: Overview. KPI cards and the monthly revenue trend."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from loaders import apply_filters, brl, insight, load

st.title("Overview")

sales = apply_filters(load("kpi_sales_cube"))
# Order-level numbers use each order's MAIN category, so an order is never counted twice.
orders = apply_filters(load("kpi_order_cube"), category_column="main_category")

if orders["orders"].sum() == 0:
    st.warning("No delivered orders match these filters. Try widening them.")
    st.stop()

# --- KPI cards ----------------------------------------------------------------------
revenue = sales["revenue"].sum()
order_count = orders["orders"].sum()
aov = orders["order_revenue"].sum() / order_count
avg_review = orders["review_score_sum"].sum() / orders["reviewed_orders"].sum()
with_date = orders[orders["delivery_status"] != "0. no delivery date"]
on_time_pct = 100 * with_date.loc[with_date["delivery_status"] == "1. on time", "orders"].sum() / with_date["orders"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Revenue", brl(revenue), help="Price + freight of delivered items")
c2.metric("Orders", f"{order_count:,}", help="Delivered orders")
c3.metric("Avg order value", brl(aov), help="Order revenue / orders")
c4.metric("Avg review", f"{avg_review:.2f} ★", help="Average review score (1–5) of delivered orders")
c5.metric("On-time delivery", f"{on_time_pct:.1f}%", help="Delivered on or before the promised date")

# --- Monthly revenue + month-over-month growth --------------------------------------
st.subheader("Monthly revenue and month-over-month growth")

monthly = sales.groupby("month", as_index=False)["revenue"].sum()
# Fill in months with no sales so "previous month" really is the previous month.
start, end = st.session_state["filter_months"]
all_months = pd.date_range(pd.Timestamp(start), pd.Timestamp(end), freq="MS")
monthly = monthly.set_index("month").reindex(all_months, fill_value=0).rename_axis("month").reset_index()
# pct_change() compares each row with the previous one: the pandas version of SQL's LAG().
monthly["mom_growth_pct"] = monthly["revenue"].pct_change() * 100

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(x=monthly["month"], y=monthly["revenue"], name="Revenue (R$)",
                     marker_color="#2E86AB", hovertemplate="%{x|%b %Y}<br>R$ %{y:,.0f}<extra></extra>"))
fig.add_trace(go.Scatter(x=monthly["month"], y=monthly["mom_growth_pct"], name="MoM growth (%)",
                         mode="lines+markers", line=dict(color="#F18F01"),
                         hovertemplate="%{x|%b %Y}<br>%{y:+.1f}%<extra></extra>"),
              secondary_y=True)
fig.update_yaxes(title_text="Revenue (R$)", secondary_y=False)
fig.update_yaxes(title_text="MoM growth (%)", secondary_y=True, zeroline=True)
fig.update_layout(height=420, legend=dict(orientation="h", y=1.1), margin=dict(t=30, b=10))
st.plotly_chart(fig, width="stretch")

insight("Revenue grew about 8× during 2017, peaked in **Nov 2017 (+54%, Black Friday)**, then "
        "**flattened at about R$ 1.0–1.13M per month in 2018**. Growth came from more orders, not bigger "
        "baskets: AOV stayed between R$ 153 and R$ 169.")
