"""Page 2: Products & Sellers. Top categories and top sellers with review score."""
import plotly.express as px
import streamlit as st

from loaders import apply_filters, brl, insight, load

st.title("Products & Sellers")

sales = apply_filters(load("kpi_sales_cube"))
sellers = apply_filters(load("kpi_seller_cube"))

if sales.empty:
    st.warning("No delivered orders match these filters. Try widening them.")
    st.stop()

top_n = st.slider("How many to show", min_value=5, max_value=20, value=10)

# --- Top categories ----------------------------------------------------------------
st.subheader(f"Top {top_n} categories by revenue")

categories = (sales.groupby("category_name", as_index=False)
              .agg(revenue=("revenue", "sum"), items_sold=("items_sold", "sum")))
categories["share_pct"] = 100 * categories["revenue"] / categories["revenue"].sum()
top_categories = categories.nlargest(top_n, "revenue")

fig = px.bar(top_categories.sort_values("revenue"), x="revenue", y="category_name", orientation="h",
             text=top_categories.sort_values("revenue")["share_pct"].map("{:.1f}%".format),
             labels={"revenue": "Revenue (R$)", "category_name": ""},
             color_discrete_sequence=["#2E86AB"])
fig.update_traces(textposition="outside",
                  hovertemplate="%{y}<br>R$ %{x:,.0f}<extra></extra>")
fig.update_layout(height=max(350, 32 * top_n), margin=dict(t=10, b=10))
st.plotly_chart(fig, width="stretch")
st.caption(f"Labels show the share of revenue in the current selection ({brl(categories['revenue'].sum())}).")

insight("No single category dominates (the top one, **health_beauty**, is 9.2%), but the **top 10 make up 62%** of "
        "revenue. **watches_gifts** earns almost as much as bed_bath_table from 40% fewer orders: high value per order.")

# --- Top sellers -------------------------------------------------------------------
st.subheader(f"Top {top_n} sellers by revenue, with average review score")

seller_summary = (sellers.groupby(["seller_id", "seller_state"], as_index=False)
                  .agg(revenue=("revenue", "sum"), orders=("orders", "sum"),
                       reviewed_orders=("reviewed_orders", "sum"), review_score_sum=("review_score_sum", "sum")))
seller_summary["avg_review"] = seller_summary["review_score_sum"] / seller_summary["reviewed_orders"]
top_sellers = seller_summary.nlargest(top_n, "revenue").copy()
# Seller IDs are long hashes; the first 8 characters are enough to tell them apart.
top_sellers["seller"] = top_sellers["seller_id"].str[:8] + " (" + top_sellers["seller_state"] + ")"

fig = px.bar(top_sellers.sort_values("revenue"), x="revenue", y="seller", orientation="h",
             color="avg_review", color_continuous_scale="RdYlGn", range_color=(3, 5),
             labels={"revenue": "Revenue (R$)", "seller": "", "avg_review": "Avg review ★"},
             hover_data={"orders": ":,", "avg_review": ":.2f"})
fig.update_layout(height=max(350, 32 * top_n), margin=dict(t=10, b=10))
st.plotly_chart(fig, width="stretch")

st.dataframe(
    top_sellers[["seller", "revenue", "orders", "avg_review", "reviewed_orders"]],
    hide_index=True, width="stretch",
    column_config={
        "seller": "Seller (state)",
        "revenue": st.column_config.NumberColumn("Revenue (R$)", format="R$ %.0f"),
        "orders": st.column_config.NumberColumn("Orders", format="%d"),
        "avg_review": st.column_config.NumberColumn("Avg review ★", format="%.2f"),
        "reviewed_orders": st.column_config.NumberColumn("Reviewed orders", format="%d"),
    },
)

insight("Most top sellers are in **São Paulo** and score 3.9–4.4 ★. The **#2 seller by revenue averages only 3.50 ★** "
        "over 967 reviewed orders: a high-revenue, high-risk account worth reviewing.")
