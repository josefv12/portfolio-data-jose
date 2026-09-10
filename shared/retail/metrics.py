"""Canonical metric definitions for the retail analytics portfolio.

Business contract:
- commercial metrics include guest sales;
- customer metrics exclude guests because they cannot be attributed to a customer.
"""

from __future__ import annotations

import pandas as pd


def revenue_total(df: pd.DataFrame) -> float:
    """Total sales revenue, including guest orders."""
    return float(df["revenue"].sum())


def total_orders(df: pd.DataFrame) -> int:
    """Number of distinct sales invoices, including guest orders."""
    return int(df["invoice_no"].nunique())


def unique_customers(df: pd.DataFrame) -> int:
    """Number of unique identified customers, excluding guests."""
    identified = df.loc[~df["is_guest"], "customer_id"]
    return int(identified.nunique())


def average_order_value(df: pd.DataFrame) -> float:
    """Average revenue per sales invoice, including guest orders."""
    order_revenue = df.groupby("invoice_no", as_index=False)["revenue"].sum()
    return float(order_revenue["revenue"].mean())


def units_sold(df: pd.DataFrame) -> int:
    """Total units sold in valid sales rows."""
    return int(df["quantity"].sum())


def return_rate_pct(sales: pd.DataFrame, returns: pd.DataFrame) -> float:
    """Returned units as a percentage of sold plus returned units."""
    sold = float(sales["quantity"].sum())
    returned = float(returns["quantity"].abs().sum())
    denominator = sold + returned
    return 0.0 if denominator == 0 else returned / denominator * 100
