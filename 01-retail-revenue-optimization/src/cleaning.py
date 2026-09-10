"""Canonical cleaning rules for the Online Retail II dataset.

The same business rules are used across the retail analytics projects:
- cancellation invoices (prefix ``C``) are separated as returns;
- non-product stock codes are excluded from sales;
- only positive quantity and price are retained for sales;
- ``Unspecified`` country records are excluded;
- guest sales are retained and marked with ``is_guest``;
- revenue is calculated as quantity * unit price.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

NON_PRODUCT_CODES = frozenset(
    {"POST", "DOT", "M", "C2", "D", "S", "BANK CHARGES"}
)


def clean_retail_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return cleaned sales and separated returns from raw Online Retail II data."""
    data = df.copy()
    data["Invoice"] = data["Invoice"].astype(str)
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")

    returns = data[data["Invoice"].str.startswith("C")].copy()
    sales = data[~data["Invoice"].str.startswith("C")].copy()

    sales = sales[~sales["StockCode"].isin(NON_PRODUCT_CODES)]
    sales = sales[sales["StockCode"].astype(str).str.match(r"^\d", na=False)]
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

    sales = _rename_columns(sales)
    returns = _rename_columns(returns)

    return sales, returns


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize the raw UCI column names to the portfolio convention."""
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


def validate_required_columns(
    columns: Iterable[str], required: Iterable[str] | None = None
) -> None:
    """Raise a clear error when the raw dataset is missing required columns."""
    required_columns = set(
        required
        or {
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
    missing = required_columns.difference(columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
