"""Olist sales dashboard: the entry point.

Run from the project root:
    streamlit run dashboard/app.py

This file sets up the page, works out the data mode, draws the sidebar filters
(shared by all pages), and then runs the page the user picked.
"""
import pandas as pd
import streamlit as st

# Must be the first Streamlit command.
st.set_page_config(page_title="Olist Sales Dashboard", page_icon="📦", layout="wide")

from loaders import load, resolve_mode, snapshot_date  # noqa: E402  (after set_page_config)

mode, reason = resolve_mode()

# --- Sidebar: filters shared by every page ------------------------------------------
st.sidebar.title("📦 Olist Sales")

sales = load("kpi_sales_cube")
months = sorted(sales["month"].dt.date.unique())
# 2016 has only a handful of orders, so start at Jan 2017 by default.
default_start = next((m for m in months if m >= pd.Timestamp("2017-01-01").date()), months[0])

st.sidebar.select_slider(
    "Purchase month",
    options=months,
    value=(default_start, months[-1]),
    format_func=lambda m: m.strftime("%b %Y"),
    key="filter_months",        # the chosen value is stored in st.session_state["filter_months"]
)
st.sidebar.multiselect(
    "Customer state",
    options=sorted(sales["customer_state"].unique()),
    placeholder="All states",
    key="filter_states",
)
st.sidebar.multiselect(
    "Product category",
    options=sorted(sales["category_name"].unique()),
    placeholder="All categories",
    key="filter_categories",
)

st.sidebar.divider()
if mode == "db":
    st.sidebar.caption("🟢 Data: live from PostgreSQL (`analytics` schema)")
else:
    st.sidebar.caption(f"📁 Data: snapshot files exported {snapshot_date() or 'unknown date'}")
st.sidebar.caption(f"Mode reason: {reason}")
st.sidebar.caption("Revenue = price + freight of delivered orders, in Brazilian reais (R$).")

# --- Pages -------------------------------------------------------------------------
page = st.navigation([
    st.Page("views/overview.py", title="Overview", icon=":material/dashboard:", default=True),
    st.Page("views/products_sellers.py", title="Products & Sellers", icon=":material/category:"),
    st.Page("views/customers_delivery.py", title="Customers & Delivery", icon=":material/local_shipping:"),
])
page.run()
