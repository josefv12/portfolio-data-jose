"""Data loading and validation for churn modeling."""

from pathlib import Path

import pandas as pd

TARGET = "churn"


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Load a CSV dataset and validate the target column."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)
    if TARGET not in df.columns:
        raise ValueError(
            f"Target column '{TARGET}' is required. Available columns: {list(df.columns)}"
        )
    if df.empty:
        raise ValueError("The dataset is empty.")
    return df
