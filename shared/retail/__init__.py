"""Shared retail analytics utilities."""

from .cleaning import clean_retail_data, validate_required_columns
from .metrics import (
    average_order_value,
    return_rate_pct,
    revenue_total,
    total_orders,
    unique_customers,
    units_sold,
)

__all__ = [
    "clean_retail_data",
    "validate_required_columns",
    "revenue_total",
    "total_orders",
    "unique_customers",
    "average_order_value",
    "units_sold",
    "return_rate_pct",
]
