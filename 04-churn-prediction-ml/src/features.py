"""Feature preparation rules for churn modeling."""

from __future__ import annotations

import pandas as pd

from src.data import TARGET

IDENTIFIER_COLUMNS = frozenset(
    {
        "customer_id",
        "customerid",
        "customer_number",
        "customer_number_id",
        "account_id",
        "accountid",
    }
)


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Remove the target and known identifier columns from model inputs."""
    if TARGET not in df.columns:
        raise ValueError(f"Target column '{TARGET}' is required.")

    drop_columns = [
        column
        for column in df.columns
        if column != TARGET and column.lower() in IDENTIFIER_COLUMNS
    ]
    return df.drop(columns=[TARGET, *drop_columns]).copy()
