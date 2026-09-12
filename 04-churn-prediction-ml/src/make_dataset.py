"""Build a customer-level churn dataset from Online Retail II."""

from __future__ import annotations

from pathlib import Path
import argparse

import pandas as pd

from src.data import TARGET

NON_PRODUCT_CODES = frozenset(
    {"POST", "DOT", "M", "C2", "D", "S", "BANK CHARGES"}
)
DEFAULT_CUTOFF = "2011-09-10"
DEFAULT_HORIZON_DAYS = 90


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Keep valid identified product sales for churn modeling."""
    required = {
        "Invoice",
        "StockCode",
        "Quantity",
        "InvoiceDate",
        "Price",
        "Customer ID",
        "Country",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data = df.copy()
    data["Invoice"] = data["Invoice"].astype(str)
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")

    data = data[~data["Invoice"].str.startswith("C")]
    stock_code = data["StockCode"].astype(str)
    data = data[~stock_code.isin(NON_PRODUCT_CODES)]
    data = data[data["StockCode"].astype(str).str.match(r"^\d", na=False)]
    data = data[(data["Price"] > 0) & (data["Quantity"] > 0)]
    data = data[data["Country"] != "Unspecified"]
    data = data[data["Customer ID"].notna()].copy()
    data["revenue"] = data["Quantity"] * data["Price"]
    return data


def build_churn_dataset(
    df: pd.DataFrame,
    cutoff: str = DEFAULT_CUTOFF,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
) -> pd.DataFrame:
    """Create one row per customer with pre-cutoff behavior and a future churn label."""
    if horizon_days <= 0:
        raise ValueError("horizon_days must be positive.")

    sales = clean_sales(df)
    cutoff_date = pd.Timestamp(cutoff)
    horizon_end = cutoff_date + pd.Timedelta(days=horizon_days)

    history = sales[sales["InvoiceDate"] < cutoff_date].copy()
    future = sales[
        (sales["InvoiceDate"] >= cutoff_date)
        & (sales["InvoiceDate"] < horizon_end)
    ]

    if history.empty:
        raise ValueError("No customer history exists before the cutoff date.")

    grouped = history.groupby("Customer ID")
    features = grouped.agg(
        recency_days=("InvoiceDate", lambda s: (cutoff_date - s.max()).days),
        frequency_orders=("Invoice", "nunique"),
        monetary_revenue=("revenue", "sum"),
        total_units=("Quantity", "sum"),
        active_months=("InvoiceDate", lambda s: s.dt.to_period("M").nunique()),
        unique_products=("StockCode", "nunique"),
        first_purchase_date=("InvoiceDate", "min"),
        last_purchase_date=("InvoiceDate", "max"),
        country=("Country", "last"),
    ).reset_index()

    features["average_order_value"] = (
        features["monetary_revenue"] / features["frequency_orders"]
    )

    units_per_order = history.groupby(["Customer ID", "Invoice"])["Quantity"].sum()
    avg_units = units_per_order.groupby(level=0).mean()
    features["avg_units_per_order"] = features["Customer ID"].map(avg_units)

    future_customers = set(future["Customer ID"].unique())
    features[TARGET] = (~features["Customer ID"].isin(future_customers)).astype(int)

    features = features.drop(columns=["first_purchase_date", "last_purchase_date"])
    features["monetary_revenue"] = features["monetary_revenue"].round(2)
    features["average_order_value"] = features["average_order_value"].round(2)
    features["avg_units_per_order"] = features["avg_units_per_order"].round(2)

    return features.sort_values("Customer ID").reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the churn modeling dataset.")
    parser.add_argument("--input", required=True, help="Path to Online Retail II CSV")
    parser.add_argument("--output", default="data/processed/churn.csv")
    parser.add_argument("--cutoff", default=DEFAULT_CUTOFF)
    parser.add_argument("--horizon-days", type=int, default=DEFAULT_HORIZON_DAYS)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    churn = build_churn_dataset(df, args.cutoff, args.horizon_days)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    churn.to_csv(output, index=False)

    print(f"Customers: {len(churn):,}")
    print(f"Churned: {int(churn[TARGET].sum()):,} ({churn[TARGET].mean():.1%})")
    print(f"Saved to: {output}")


if __name__ == "__main__":
    main()
