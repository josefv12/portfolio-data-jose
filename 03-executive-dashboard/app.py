import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Online Retail Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_dotenv()

# ── DB connection ───────────────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    """Connect to PostgreSQL. Falls back to CSV if DB is unavailable."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine
        except Exception:
            return None
    return None


@st.cache_data(ttl=600)
def load_data():
    engine = get_engine()
    if engine:
        with engine.connect() as conn:
            df = pd.read_sql(
                "SELECT * FROM online_retail_clean", conn
            )
            ret = pd.read_sql(
                "SELECT * FROM online_retail_returns", conn
            )
    else:
        import os

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        df = pd.read_csv(os.path.join(BASE_DIR, "data/processed/online_retail_clean.csv"))
        ret = pd.read_csv(os.path.join(BASE_DIR, "data/processed/online_retail_returns.csv"))
       

    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    ret["invoice_date"] = pd.to_datetime(ret["invoice_date"])
    df["year_month"] = df["invoice_date"].dt.to_period("M").astype(str)
    return df, ret


# ── Helpers ─────────────────────────────────────────────────────────────────────
PALETTE = px.colors.qualitative.Bold
KPI_STYLE = """
<style>
    .kpi-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 20px 24px;
        border-left: 4px solid {color};
    }
    .kpi-label { color: #a0a0b0; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value { color: #ffffff; font-size: 32px; font-weight: 700; margin: 4px 0; }
    .kpi-delta { font-size: 13px; }
</style>
"""


def fmt_currency(val):
    if val >= 1_000_000:
        return f"£{val/1_000_000:.2f}M"
    if val >= 1_000:
        return f"£{val/1_000:.1f}K"
    return f"£{val:.0f}"


def kpi_card(label, value, delta=None, color="#6c63ff"):
    delta_html = ""
    if delta is not None:
        arrow = "▲" if delta >= 0 else "▼"
        clr = "#22c55e" if delta >= 0 else "#ef4444"
        delta_html = f'<div class="kpi-delta" style="color:{clr}">{arrow} {abs(delta):.1f}% vs prev period</div>'
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left-color:{color}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Load data ────────────────────────────────────────────────────────────────────
df_raw, ret_raw = load_data()

# ── Sidebar filters ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shopping-cart.png", width=60)
    st.title("Online Retail")
    st.caption("Executive Dashboard · 2009–2011")
    st.divider()

    years = sorted(df_raw["year"].unique())
    sel_years = st.multiselect("Year", years, default=years)

    countries_all = sorted(df_raw["country"].unique())
    sel_countries = st.multiselect(
        "Country",
        countries_all,
        default=["United Kingdom", "Germany", "France", "EIRE", "Netherlands"],
    )

    st.divider()
    st.caption("Portfolio project by **Jose** · [GitHub](https://github.com)")

# ── Filter data ──────────────────────────────────────────────────────────────────
df = df_raw[df_raw["year"].isin(sel_years)].copy()
ret = ret_raw[
    ret_raw["invoice_date"].dt.year.isin(sel_years)
].copy()

df_geo = df_raw[df_raw["year"].isin(sel_years)].copy()  # geo always uses all countries
df = df[df["country"].isin(sel_countries)] if sel_countries else df

# ── KPIs ──────────────────────────────────────────────────────────────────────────
total_revenue = df["revenue"].sum()
total_orders = df["invoice_no"].nunique()
total_customers = df["customer_id"].nunique()
return_rate = len(ret) / (len(df) + len(ret)) * 100
avg_order = df.groupby("invoice_no")["revenue"].sum().mean()

st.markdown(KPI_STYLE, unsafe_allow_html=True)
st.markdown("## 📊 Executive Dashboard")
st.caption(f"Showing data for: **{', '.join(map(str, sel_years))}** · **{len(sel_countries)} countries selected**")
st.markdown("")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi_card("Total Revenue", fmt_currency(total_revenue), color="#6c63ff")
with c2:
    kpi_card("Total Orders", f"{total_orders:,}", color="#06b6d4")
with c3:
    kpi_card("Unique Customers", f"{total_customers:,}", color="#f59e0b")
with c4:
    kpi_card("Avg Order Value", fmt_currency(avg_order), color="#10b981")
with c5:
    kpi_card("Return Rate", f"{return_rate:.1f}%", color="#ef4444")

st.markdown("---")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Revenue Trends", "🏆 Products", "👥 Customers", "↩️ Returns"]
)

# ═══ TAB 1: Revenue Trends ═══════════════════════════════════════════════════
with tab1:
    col_l, col_r = st.columns([2, 1])

    with col_l:
        # Monthly revenue line chart
        monthly = (
            df.groupby("year_month")["revenue"]
            .sum()
            .reset_index()
            .sort_values("year_month")
        )
        fig_trend = px.line(
            monthly,
            x="year_month",
            y="revenue",
            title="Monthly Revenue Trend",
            markers=True,
            color_discrete_sequence=["#6c63ff"],
        )
        fig_trend.update_layout(
            xaxis_title="Month",
            yaxis_title="Revenue (£)",
            yaxis_tickformat=",.0f",
            hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        fig_trend.update_xaxes(tickangle=45)
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_r:
        # Revenue by year donut
        yearly = df.groupby("year")["revenue"].sum().reset_index()
        fig_donut = px.pie(
            yearly,
            names="year",
            values="revenue",
            hole=0.55,
            title="Revenue by Year",
            color_discrete_sequence=PALETTE,
        )
        fig_donut.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # Revenue by country bar
    country_rev = (
        df.groupby("country")["revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    fig_country = px.bar(
        country_rev,
        x="country",
        y="revenue",
        title="Top 10 Countries by Revenue",
        color="revenue",
        color_continuous_scale="Purples",
    )
    fig_country.update_layout(
        yaxis_tickformat=",.0f",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_country, use_container_width=True)

    # Heatmap: revenue by month & year
    pivot = (
        df.groupby(["year", "month"])["revenue"]
        .sum()
        .reset_index()
        .pivot(index="year", columns="month", values="revenue")
    )
    month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                   7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    pivot.columns = [month_names[m] for m in pivot.columns]
    fig_heat = px.imshow(
        pivot,
        title="Revenue Heatmap by Month & Year",
        color_continuous_scale="Purples",
        text_auto=".2s",
        aspect="auto",
    )
    fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_heat, use_container_width=True)


# ═══ TAB 2: Products ═════════════════════════════════════════════════════════
with tab2:
    col_a, col_b = st.columns(2)

    with col_a:
        top_products_rev = (
            df.groupby("description")["revenue"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        fig_p1 = px.bar(
            top_products_rev,
            x="revenue",
            y="description",
            orientation="h",
            title="Top 10 Products by Revenue",
            color="revenue",
            color_continuous_scale="Teal",
        )
        fig_p1.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_tickformat=",.0f",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_p1, use_container_width=True)

    with col_b:
        top_products_qty = (
            df.groupby("description")["quantity"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        fig_p2 = px.bar(
            top_products_qty,
            x="quantity",
            y="description",
            orientation="h",
            title="Top 10 Products by Units Sold",
            color="quantity",
            color_continuous_scale="Oranges",
        )
        fig_p2.update_layout(
            yaxis={"categoryorder": "total ascending"},
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_p2, use_container_width=True)

    # Price vs quantity scatter (top 200 products)
    product_stats = (
        df.groupby("description")
        .agg(total_revenue=("revenue", "sum"),
             total_qty=("quantity", "sum"),
             avg_price=("unit_price", "mean"))
        .sort_values("total_revenue", ascending=False)
        .head(200)
        .reset_index()
    )
    fig_scatter = px.scatter(
        product_stats,
        x="avg_price",
        y="total_qty",
        size="total_revenue",
        color="total_revenue",
        hover_name="description",
        title="Price vs Units Sold (bubble = revenue) — Top 200 Products",
        color_continuous_scale="Viridis",
        log_x=True,
        log_y=True,
    )
    fig_scatter.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)


# ═══ TAB 3: Customers ════════════════════════════════════════════════════════
with tab3:
    col_x, col_y = st.columns(2)

    with col_x:
        # Guest vs registered
        guest_data = df.groupby("is_guest")["revenue"].sum().reset_index()
        guest_data["type"] = guest_data["is_guest"].map(
            {True: "Guest", False: "Registered"}
        )
        fig_guest = px.pie(
            guest_data,
            names="type",
            values="revenue",
            title="Revenue: Guest vs Registered Customers",
            color_discrete_sequence=["#6c63ff", "#06b6d4"],
            hole=0.4,
        )
        fig_guest.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_guest, use_container_width=True)

    with col_y:
        # Top 10 customers by revenue
        top_customers = (
            df[df["customer_id"].notna()]
            .groupby("customer_id")["revenue"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        top_customers["customer_id"] = "Customer " + top_customers["customer_id"].astype(int).astype(str)
        fig_cust = px.bar(
            top_customers,
            x="revenue",
            y="customer_id",
            orientation="h",
            title="Top 10 Customers by Revenue",
            color="revenue",
            color_continuous_scale="Blues",
        )
        fig_cust.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_tickformat=",.0f",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_cust, use_container_width=True)

    # New customers per month
    first_purchase = (
        df[df["customer_id"].notna()]
        .groupby("customer_id")["invoice_date"]
        .min()
        .reset_index()
    )
    first_purchase["year_month"] = first_purchase["invoice_date"].dt.to_period("M").astype(str)
    new_monthly = first_purchase.groupby("year_month").size().reset_index(name="new_customers")
    new_monthly = new_monthly.sort_values("year_month")

    fig_new = px.bar(
        new_monthly,
        x="year_month",
        y="new_customers",
        title="New Customers Acquired per Month",
        color_discrete_sequence=["#10b981"],
    )
    fig_new.update_layout(
        xaxis_title="Month",
        yaxis_title="New Customers",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig_new.update_xaxes(tickangle=45)
    st.plotly_chart(fig_new, use_container_width=True)


# ═══ TAB 4: Returns ══════════════════════════════════════════════════════════
with tab4:
    col_m, col_n = st.columns(2)

    with col_m:
        # Returns by country
        ret_country = (
            ret.groupby("country")
            .size()
            .sort_values(ascending=False)
            .head(10)
            .reset_index(name="return_count")
        )
        fig_ret_country = px.bar(
            ret_country,
            x="return_count",
            y="country",
            orientation="h",
            title="Top 10 Countries by Return Volume",
            color="return_count",
            color_continuous_scale="Reds",
        )
        fig_ret_country.update_layout(
            yaxis={"categoryorder": "total ascending"},
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_ret_country, use_container_width=True)

    with col_n:
        # Most returned products
        ret_products = (
            ret.groupby("description")
            .size()
            .sort_values(ascending=False)
            .head(10)
            .reset_index(name="return_count")
        )
        fig_ret_prod = px.bar(
            ret_products,
            x="return_count",
            y="description",
            orientation="h",
            title="Most Returned Products",
            color="return_count",
            color_continuous_scale="OrRd",
        )
        fig_ret_prod.update_layout(
            yaxis={"categoryorder": "total ascending"},
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_ret_prod, use_container_width=True)

    # Monthly return trend
    ret["year_month"] = ret["invoice_date"].dt.to_period("M").astype(str)
    ret_monthly = ret.groupby("year_month").size().reset_index(name="returns")
    ret_monthly = ret_monthly.sort_values("year_month")

    fig_ret_trend = px.area(
        ret_monthly,
        x="year_month",
        y="returns",
        title="Monthly Return Volume Trend",
        color_discrete_sequence=["#ef4444"],
    )
    fig_ret_trend.update_layout(
        xaxis_title="Month",
        yaxis_title="Number of Returns",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig_ret_trend.update_xaxes(tickangle=45)
    st.plotly_chart(fig_ret_trend, use_container_width=True)
