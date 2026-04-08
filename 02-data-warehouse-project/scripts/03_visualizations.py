"""
Proyecto 2 — Online Retail II
Paso 3: Visualizaciones desde PostgreSQL
Archivo: scripts/03_visualizations.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sqlalchemy import create_engine
from pathlib import Path

# ──────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "retail_db",
    "user":     "postgres",
    "password": "admin123",
    "schema":   "retail",
}

BASE_DIR    = Path(__file__).resolve().parent.parent
OUTPUT_DIR  = BASE_DIR / "screenshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Estilo global
plt.rcParams.update({
    "figure.facecolor":  "#FAFAFA",
    "axes.facecolor":    "#FAFAFA",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.3,
    "grid.linestyle":    "--",
    "font.family":       "sans-serif",
    "font.size":         11,
})
PALETTE = ["#185FA5", "#1D9E75", "#D85A30", "#7F77DD", "#BA7517"]


def get_engine():
    url = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    )
    return create_engine(url)


def save(fig, name):
    path = OUTPUT_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Guardado: screenshots/{name}")


# ──────────────────────────────────────────────
# CHART 1 — Revenue mensual con tendencia
# ──────────────────────────────────────────────
def chart_monthly_revenue(engine):
    df = pd.read_sql(
        "SELECT year, month, period, revenue, avg_order_value "
        "FROM retail.vw_monthly_revenue ORDER BY year, month",
        engine
    )
    df["label"] = df["period"].str[:3] + "\n" + df["year"].astype(str).str[-2:]

    fig, ax1 = plt.subplots(figsize=(14, 5))

    bars = ax1.bar(df.index, df["revenue"] / 1000,
                   color=PALETTE[0], alpha=0.85, width=0.6)
    ax1.set_ylabel("Revenue (£ miles)", color=PALETTE[0])
    ax1.set_xticks(df.index)
    ax1.set_xticklabels(df["label"], fontsize=9)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"£{x:,.0f}k"))

    ax2 = ax1.twinx()
    ax2.plot(df.index, df["avg_order_value"], color=PALETTE[2],
             linewidth=2, marker="o", markersize=4, label="Ticket promedio")
    ax2.set_ylabel("Ticket promedio (£)", color=PALETTE[2])
    ax2.spines["top"].set_visible(False)

    # Anotar pico de revenue
    peak = df["revenue"].idxmax()
    ax1.annotate(
        f"Pico: £{df.loc[peak,'revenue']/1000:,.0f}k",
        xy=(peak, df.loc[peak, "revenue"] / 1000),
        xytext=(peak - 2, df.loc[peak, "revenue"] / 1000 + 30),
        arrowprops=dict(arrowstyle="->", color="gray"),
        fontsize=9, color="gray"
    )

    ax1.set_title("Revenue mensual y ticket promedio — Online Retail II",
                  fontsize=13, pad=14)
    fig.tight_layout()
    save(fig, "01_monthly_revenue.png")


# ──────────────────────────────────────────────
# CHART 2 — Top 10 clientes
# ──────────────────────────────────────────────
def chart_top_customers(engine):
    df = pd.read_sql(
        "SELECT customer_id, country, monetary AS total_revenue, frequency AS total_invoices "
        "FROM retail.vw_customer_rfm "
        "ORDER BY monetary DESC LIMIT 10",
        engine
    )
    df["label"] = df["customer_id"].astype(str) + "\n(" + df["country"] + ")"

    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.barh(df["label"][::-1], df["total_revenue"][::-1] / 1000,
                   color=PALETTE[1], alpha=0.85)
    ax.set_xlabel("Revenue total (£ miles)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"£{x:,.0f}k"))
    ax.set_title("Top 10 clientes por revenue total", fontsize=13, pad=14)

    for bar, val in zip(bars, df["total_revenue"][::-1]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"£{val/1000:,.1f}k", va="center", fontsize=9, color="gray")

    fig.tight_layout()
    save(fig, "02_top_customers.png")


# ──────────────────────────────────────────────
# CHART 3 — Pareto de productos (curva 80/20)
# ──────────────────────────────────────────────
def chart_pareto(engine):
    df = pd.read_sql(
        "SELECT revenue_rank, total_revenue AS revenue, cumulative_pct "
        "FROM retail.vw_top_products "
        "ORDER BY revenue_rank",
        engine
    )

    # Solo mostrar hasta donde la curva llega al 85% para que el gráfico sea legible
    df_plot = df[df["cumulative_pct"] <= 85].copy()

    fig, ax1 = plt.subplots(figsize=(12, 5))

    ax1.bar(df_plot["revenue_rank"], df_plot["revenue"] / 1000,
            color=PALETTE[0], alpha=0.7, width=1)
    ax1.set_xlabel("Productos (ordenados por revenue)")
    ax1.set_ylabel("Revenue (£ miles)", color=PALETTE[0])
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"£{x:,.0f}k"))

    ax2 = ax1.twinx()
    ax2.plot(df_plot["revenue_rank"], df_plot["cumulative_pct"],
             color=PALETTE[2], linewidth=2)
    ax2.axhline(80, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax2.set_ylabel("% acumulado del revenue", color=PALETTE[2])
    ax2.set_ylim(0, 105)
    ax2.spines["top"].set_visible(False)

    # Línea vertical y anotación en el corte 80%
    cutoff = df[df["cumulative_pct"] <= 80]["revenue_rank"].max()
    ax1.axvline(cutoff, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax1.text(cutoff + 2, ax1.get_ylim()[1] * 0.85,
             f"{cutoff} productos\n= 80% del revenue",
             fontsize=9, color="gray")

    x_max = df_plot["revenue_rank"].max()
    ax2.text(x_max * 0.95, 81, "80%", fontsize=9, color="gray")
    ax1.set_title("Análisis Pareto — concentración de revenue en productos",
                  fontsize=13, pad=14)
    fig.tight_layout()
    save(fig, "03_pareto_products.png")


# ──────────────────────────────────────────────
# CHART 4 — Revenue por país (top 10 sin UK)
# ──────────────────────────────────────────────
def chart_by_country(engine):
    df = pd.read_sql(
        "SELECT country, total_revenue, avg_order_value, unique_customers "
        "FROM retail.vw_revenue_by_country "
        "WHERE country != 'United Kingdom' "
        "ORDER BY total_revenue DESC LIMIT 10",
        engine
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Revenue total
    ax1.barh(df["country"][::-1], df["total_revenue"][::-1] / 1000,
             color=PALETTE[3], alpha=0.85)
    ax1.set_xlabel("Revenue (£ miles)")
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"£{x:,.0f}k"))
    ax1.set_title("Revenue total por país\n(excl. UK)", fontsize=12)

    # Ticket promedio
    ax2.barh(df["country"][::-1], df["avg_order_value"][::-1],
             color=PALETTE[4], alpha=0.85)
    ax2.set_xlabel("Ticket promedio (£)")
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"£{x:,.0f}"))
    ax2.set_title("Ticket promedio por país\n(excl. UK)", fontsize=12)

    fig.suptitle("Mercados internacionales — Top 10", fontsize=13, y=1.02)
    fig.tight_layout()
    save(fig, "04_revenue_by_country.png")


# ──────────────────────────────────────────────
# CHART 5 — Distribución de segmentos RFM
# ──────────────────────────────────────────────
def chart_rfm_segments(engine):
    df = pd.read_sql(
        "SELECT segment, COUNT(*) AS customers, "
        "ROUND(AVG(monetary)::NUMERIC, 0) AS avg_revenue "
        "FROM retail.vw_customer_rfm "
        "GROUP BY segment ORDER BY customers DESC",
        engine
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    colors = [PALETTE[i % len(PALETTE)] for i in range(len(df))]

    # Donut — cantidad de clientes
    wedges, texts, autotexts = ax1.pie(
        df["customers"],
        labels=df["segment"],
        autopct="%1.1f%%",
        colors=colors,
        startangle=90,
        wedgeprops={"width": 0.55, "edgecolor": "white", "linewidth": 2},
        textprops={"fontsize": 9},
    )
    ax1.set_title("Distribución de clientes\npor segmento RFM", fontsize=12)

    # Barras — revenue promedio por segmento (mismo orden que el donut)
    ax2.bar(range(len(df)), df["avg_revenue"],
            color=colors, alpha=0.85)
    ax2.set_ylabel("Revenue promedio (£)")
    ax2.set_xticks(range(len(df)))
    ax2.set_xticklabels(df["segment"], rotation=20, ha="right", fontsize=9)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"£{x:,.0f}"))
    ax2.set_title("Revenue promedio\npor segmento RFM", fontsize=12)

    fig.suptitle("Segmentación RFM de clientes", fontsize=13, y=1.02)
    fig.tight_layout()
    save(fig, "05_rfm_segments.png")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    print("\n" + "="*50)
    print("GENERANDO VISUALIZACIONES")
    print("="*50 + "\n")
    engine = get_engine()

    chart_monthly_revenue(engine)
    chart_top_customers(engine)
    chart_pareto(engine)
    chart_by_country(engine)
    chart_rfm_segments(engine)

    print(f"\n5 gráficos guardados en screenshots/")


if __name__ == "__main__":
    main()
