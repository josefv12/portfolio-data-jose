"""Canonical cleaning rules for the Online Retail II dataset."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

NON_PRODUCT_CODES = frozenset(
    {"POST", "DOT", "M", "C2", "D", "S", "BANK CHARGES"}
)

REQUIRED_COLUMNS = frozenset(
    {
        "Invoice",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "Price",
        "Customer ID",
        "Country",
    }
)


def validate_required_columns(
    columns: Iterable[str], required: Iterable[str] = REQUIRED_COLUMNS
) -> None:
    """Raise a clear error when the raw dataset is missing required columns."""
    missing = set(required).difference(columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def clean_retail_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean raw Online Retail II data and separate cancellation invoices."""
    validate_required_columns(df.columns)

    data = df.copy()
    data["Invoice"] = data["Invoice"].astype(str)
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")

    returns = data[data["Invoice"].str.startswith("C")].copy()
    sales = data[~data["Invoice"].str.startswith("C")].copy()

    stock_code = sales["StockCode"].astype(str)
    sales = sales[~stock_code.isin(NON_PRODUCT_CODES)]
    sales = sales[stock_code.str.match(r"^\d", na=False)]
    sales = sales[(sales["Price"] > 0) & (sales["Quantity"] > 0)]
    sales = sales[sales["Country"] != "Unspecified"]

    desc_map = (
        sales.dropna(subset=["Description"])
        .groupby("StockCode")["Description"]
        .agg(lambda values: values.mode().iloc[0])
    )
    sales["Description"] = sales["Description"].fillna(
        sales["StockCode"].map(desc_map)
    )

    sales["is_guest"] = sales["Customer ID"].isna()
    sales["Revenue"] = (sales["Quantity"] * sales["Price"]).round(2)
    sales["Year"] = sales["InvoiceDate"].dt.year
    sales["Month"] = sales["InvoiceDate"].dt.month

    return _normalize_columns(sales), _normalize_columns(returns)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(
        columns={
            "Invoice": "invoice_no",
            "StockCode": "stock_code",
            "Description": "description",
            "Quantity": "quantity",
            "InvoiceDate": "invoice_date",
            "Price": "unit_price",
            "Customer ID": "customer_id",
            "Country": "country",
            "Revenue": "revenue",
            "Year": "year",
            "Month": "month",
        }
    )
