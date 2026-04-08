import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
            df = pd.read_sql("SELECT * FROM online_retail_clean", conn)
            ret = pd.read_sql("SELECT * FROM online_retail_returns", conn)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        df  = pd.read_csv(os.path.join(BASE_DIR, "data/processed/sample_clean.csv"))
        ret = pd.read_csv(os.path.join(BASE_DIR, "data/processed/sample_returns.csv"))
        
    df["invoice_date"]  = pd.to_datetime(df["invoice_date"])
    ret["invoice_date"] = pd.to_datetime(ret["invoice_date"])
    df["year_month"]    = df["invoice_date"].dt.to_period("M").astype(str)
    ret["year_month"]   = ret["invoice_date"].dt.to_period("M").astype(str)
    ret["year"]         = ret["invoice_date"].dt.year
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
        clr   = "#22c55e" if delta >= 0 else "#ef4444"
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


# ── Load raw data ────────────────────────────────────────────────────────────────
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
    st.caption("Portfolio project by **Jose** · [GitHub](https://github.com/josefv12/portfolio-data-jose)")

# ── Filter data — mismo filtro para ventas Y devoluciones ───────────────────────
df = df_raw[df_raw["year"].isin(sel_years)].copy()
if sel_countries:
    df = df[df["country"].isin(sel_countries)]

ret = ret_raw[ret_raw["year"].isin(sel_years)].copy()
if sel_countries:
    ret = ret[ret["country"].isin(sel_countries)]

# ── KPIs ──────────────────────────────────────────────────────────────────────────
total_revenue    = df["revenue"].sum()
total_orders     = df["invoice_no"].nunique()
total_customers  = df[~df["is_guest"]]["customer_id"].nunique()
avg_order        = df.groupby("invoice_no")["revenue"].sum().mean()

# Return rate: unidades devueltas / (unidades vendidas + devueltas)
units_sold       = df["quantity"].sum()
units_returned   = ret["quantity"].abs().sum()
return_rate      = (units_returned / (units_sold + units_returned) * 100) if (units_sold + units_returned) > 0 else 0

st.markdown(KPI_STYLE, unsafe_allow_html=True)
st.markdown("## 📊 Executive Dashboard")
countries_label = f"{len(sel_countries)} countries selected" if sel_countries else "All countries"
st.caption(f"Showing data for: **{', '.join(map(str, sel_years))}** · **{countries_label}**")
st.markdown("")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi_card("Total Revenue",     fmt_currency(total_revenue), color="#6c63ff")
with c2:
    kpi_card("Total Orders",      f"{total_orders:,}",         color="#06b6d4")
with c3:
    kpi_card("Unique Customers",  f"{total_customers:,}",      color="#f59e0b")
with c4:
    kpi_card("Avg Order Value",   fmt_currency(avg_order),     color="#10b981")
with c5:
    kpi_card("Return Rate",       f"{return_rate:.1f}%",       color="#ef4444")

st.markdown("---")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Revenue Trends", "🏆 Products", "👥 Customers", "↩️ Returns"]
)

LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)

# ═══ TAB 1: Revenue Trends ═══════════════════════════════════════════════════
with tab1:
    col_l, col_r = st.columns([2, 1])

    with col_l:
        monthly = (
            df.groupby("year_month")["revenue"]
            .sum()
            .reset_index()
            .sort_values("year_month")
        )
        # Rolling average 3 meses para suavizar la tendencia
        monthly["rolling_avg"] = monthly["revenue"].rolling(3, min_periods=1).mean()

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=monthly["year_month"], y=monthly["revenue"],
            name="Revenue", marker_color="#6c63ff", opacity=0.6,
        ))
        fig_trend.add_trace(go.Scatter(
            x=monthly["year_month"], y=monthly["rolling_avg"],
            name="3-month avg", line=dict(color="#f59e0b", width=2.5),
            mode="lines",
        ))
        fig_trend.update_layout(
            title="Monthly Revenue Trend",
            xaxis_title="Month", yaxis_title="Revenue (£)",
            yaxis_tickformat=",.0f",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1),
            **LAYOUT,
        )
        fig_trend.update_xaxes(tickangle=45)
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_r:
        yearly = df.groupby("year")["revenue"].sum().reset_index()
        fig_donut = px.pie(
            yearly, names="year", values="revenue",
            hole=0.55, title="Revenue by Year",
            color_discrete_sequence=PALETTE,
        )
        fig_donut.update_layout(**LAYOUT)
        st.plotly_chart(fig_donut, use_container_width=True)

    # Revenue by country
    country_rev = (
        df.groupby("country")["revenue"]
        .sum().sort_values(ascending=False).head(10).reset_index()
    )
    fig_country = px.bar(
        country_rev, x="country", y="revenue",
        title="Top 10 Countries by Revenue",
        color="revenue", color_continuous_scale="Purples",
    )
    fig_country.update_layout(
        yaxis_tickformat=",.0f", coloraxis_showscale=False, **LAYOUT
    )
    st.plotly_chart(fig_country, use_container_width=True)

    # Heatmap revenue por mes y año
    pivot = (
        df.groupby(["year", "month"])["revenue"]
        .sum().reset_index()
        .pivot(index="year", columns="month", values="revenue")
    )
    month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                   7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    pivot.columns = [month_names[m] for m in pivot.columns]
    fig_heat = px.imshow(
        pivot, title="Revenue Heatmap — Month × Year",
        color_continuous_scale="Purples",
        text_auto=".2s", aspect="auto",
    )
    fig_heat.update_layout(**LAYOUT)
    st.plotly_chart(fig_heat, use_container_width=True)


# ═══ TAB 2: Products ═════════════════════════════════════════════════════════
with tab2:
    col_a, col_b = st.columns(2)

    with col_a:
        top_rev = (
            df.groupby("description")["revenue"]
            .sum().sort_values(ascending=False).head(10).reset_index()
        )
        fig_p1 = px.bar(
            top_rev, x="revenue", y="description", orientation="h",
            title="Top 10 Products by Revenue",
            color="revenue", color_continuous_scale="Teal",
        )
        fig_p1.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_tickformat=",.0f", coloraxis_showscale=False, **LAYOUT,
        )
        st.plotly_chart(fig_p1, use_container_width=True)

    with col_b:
        top_qty = (
            df.groupby("description")["quantity"]
            .sum().sort_values(ascending=False).head(10).reset_index()
        )
        fig_p2 = px.bar(
            top_qty, x="quantity", y="description", orientation="h",
            title="Top 10 Products by Units Sold",
            color="quantity", color_continuous_scale="Oranges",
        )
        fig_p2.update_layout(
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False, **LAYOUT,
        )
        st.plotly_chart(fig_p2, use_container_width=True)

    # Pareto — curva acumulada
    pareto = (
        df.groupby("description")["revenue"]
        .sum().sort_values(ascending=False).reset_index()
    )
    pareto["cumulative_pct"] = pareto["revenue"].cumsum() / pareto["revenue"].sum() * 100
    pareto["rank"] = range(1, len(pareto) + 1)
    cutoff_80 = pareto[pareto["cumulative_pct"] <= 80]["rank"].max()

    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Bar(
        x=pareto["rank"].head(300), y=pareto["revenue"].head(300),
        name="Revenue", marker_color="#6c63ff", opacity=0.7,
    ))
    fig_pareto.add_trace(go.Scatter(
        x=pareto["rank"].head(300), y=pareto["cumulative_pct"].head(300),
        name="Cumulative %", yaxis="y2",
        line=dict(color="#f59e0b", width=2),
    ))
    fig_pareto.add_hline(y=80, line_dash="dash", line_color="gray",
                         annotation_text="80%", yref="y2")
    fig_pareto.add_vline(x=cutoff_80, line_dash="dash", line_color="gray",
                         annotation_text=f"{cutoff_80} products")
    fig_pareto.update_layout(
        title=f"Pareto — {cutoff_80} products generate 80% of revenue",
        xaxis_title="Products (ranked by revenue)",
        yaxis_title="Revenue (£)",
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1),
        **LAYOUT,
    )
    st.plotly_chart(fig_pareto, use_container_width=True)

    # Scatter precio vs cantidad
    product_stats = (
        df.groupby("description")
        .agg(total_revenue=("revenue","sum"),
             total_qty=("quantity","sum"),
             avg_price=("unit_price","mean"))
        .sort_values("total_revenue", ascending=False)
        .head(200).reset_index()
    )
    fig_scatter = px.scatter(
        product_stats, x="avg_price", y="total_qty",
        size="total_revenue", color="total_revenue",
        hover_name="description",
        title="Price vs Units Sold (bubble = revenue) — Top 200 Products",
        color_continuous_scale="Viridis", log_x=True, log_y=True,
    )
    fig_scatter.update_layout(**LAYOUT)
    st.plotly_chart(fig_scatter, use_container_width=True)


# ═══ TAB 3: Customers ════════════════════════════════════════════════════════
with tab3:
    col_x, col_y = st.columns(2)

    with col_x:
        guest_data = df.groupby("is_guest")["revenue"].sum().reset_index()
        guest_data["type"] = guest_data["is_guest"].map(
            {True: "Guest", False: "Registered"}
        )
        fig_guest = px.pie(
            guest_data, names="type", values="revenue",
            title="Revenue: Guest vs Registered Customers",
            color_discrete_sequence=["#6c63ff", "#06b6d4"], hole=0.4,
        )
        fig_guest.update_layout(**LAYOUT)
        st.plotly_chart(fig_guest, use_container_width=True)

    with col_y:
        top_customers = (
            df[~df["is_guest"]]
            .groupby("customer_id")["revenue"]
            .sum().sort_values(ascending=False).head(10).reset_index()
        )
        top_customers["customer_id"] = (
            "Customer " + top_customers["customer_id"].astype(int).astype(str)
        )
        fig_cust = px.bar(
            top_customers, x="revenue", y="customer_id", orientation="h",
            title="Top 10 Customers by Revenue",
            color="revenue", color_continuous_scale="Blues",
        )
        fig_cust.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_tickformat=",.0f", coloraxis_showscale=False, **LAYOUT,
        )
        st.plotly_chart(fig_cust, use_container_width=True)

    # Nuevos clientes por mes
    first_purchase = (
        df[~df["is_guest"]]
        .groupby("customer_id")["invoice_date"].min().reset_index()
    )
    first_purchase["year_month"] = (
        first_purchase["invoice_date"].dt.to_period("M").astype(str)
    )
    new_monthly = (
        first_purchase.groupby("year_month").size()
        .reset_index(name="new_customers")
        .sort_values("year_month")
    )
    fig_new = px.bar(
        new_monthly, x="year_month", y="new_customers",
        title="New Customers Acquired per Month",
        color_discrete_sequence=["#10b981"],
    )
    fig_new.update_layout(
        xaxis_title="Month", yaxis_title="New Customers", **LAYOUT
    )
    fig_new.update_xaxes(tickangle=45)
    st.plotly_chart(fig_new, use_container_width=True)

    # Distribución de revenue por cliente (histograma)
    customer_rev = (
        df[~df["is_guest"]]
        .groupby("customer_id")["revenue"].sum().reset_index()
    )
    fig_hist = px.histogram(
        customer_rev, x="revenue", nbins=50,
        title="Distribution of Revenue per Customer",
        color_discrete_sequence=["#6c63ff"],
        log_y=True,
    )
    fig_hist.update_layout(
        xaxis_title="Total Revenue (£)",
        yaxis_title="Number of Customers (log scale)",
        **LAYOUT,
    )
    st.plotly_chart(fig_hist, use_container_width=True)


# ═══ TAB 4: Returns ══════════════════════════════════════════════════════════
with tab4:

    if ret.empty:
        st.info("No return data for the selected filters.")
    else:
        # Métricas de devoluciones
        r1, r2, r3 = st.columns(3)
        with r1:
            kpi_card("Total Returns",    f"{len(ret):,}",                   color="#ef4444")
        with r2:
            rev_lost = (ret["quantity"].abs() * ret["unit_price"]).sum()
            kpi_card("Revenue Lost",     fmt_currency(rev_lost),            color="#ef4444")
        with r3:
            kpi_card("Return Rate",      f"{return_rate:.2f}% of units",    color="#ef4444")

        st.markdown("")

        col_m, col_n = st.columns(2)

        with col_m:
            ret_country = (
                ret.groupby("country").size()
                .sort_values(ascending=False).head(10)
                .reset_index(name="return_count")
            )
            fig_ret_c = px.bar(
                ret_country, x="return_count", y="country", orientation="h",
                title="Top 10 Countries by Return Volume",
                color="return_count", color_continuous_scale="Reds",
            )
            fig_ret_c.update_layout(
                yaxis={"categoryorder": "total ascending"},
                coloraxis_showscale=False, **LAYOUT,
            )
            st.plotly_chart(fig_ret_c, use_container_width=True)

        with col_n:
            ret_prod = (
                ret[ret["description"].notna()]
                .groupby("description").size()
                .sort_values(ascending=False).head(10)
                .reset_index(name="return_count")
            )
            fig_ret_p = px.bar(
                ret_prod, x="return_count", y="description", orientation="h",
                title="Most Returned Products",
                color="return_count", color_continuous_scale="OrRd",
            )
            fig_ret_p.update_layout(
                yaxis={"categoryorder": "total ascending"},
                coloraxis_showscale=False, **LAYOUT,
            )
            st.plotly_chart(fig_ret_p, use_container_width=True)

        # Tendencia mensual de devoluciones
        ret_monthly = (
            ret.groupby("year_month").size()
            .reset_index(name="returns")
            .sort_values("year_month")
        )
        fig_ret_trend = px.area(
            ret_monthly, x="year_month", y="returns",
            title="Monthly Return Volume Trend",
            color_discrete_sequence=["#ef4444"],
        )
        fig_ret_trend.update_layout(
            xaxis_title="Month", yaxis_title="Number of Returns", **LAYOUT
        )
        fig_ret_trend.update_xaxes(tickangle=45)
        st.plotly_chart(fig_ret_trend, use_container_width=True)