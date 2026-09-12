import pandas as pd
import pytest

from src.make_dataset import build_churn_dataset, clean_sales


def sample_transactions() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Invoice": ["10001", "10002", "C10003", "10004", "10005", "10006"],
            "StockCode": ["100", "101", "102", "POST", "103", "ABC"],
            "Quantity": [2, 3, 1, 1, -2, 1],
            "InvoiceDate": [
                "2011-08-01",
                "2011-08-15",
                "2011-08-20",
                "2011-08-21",
                "2011-08-22",
                "2011-08-23",
            ],
            "Price": [10, 20, 30, 5, 10, 5],
            "Customer ID": [1, 1, 2, 1, 2, None],
            "Country": ["United Kingdom"] * 6,
        }
    )


def test_clean_sales_keeps_only_valid_identified_product_sales():
    sales = clean_sales(sample_transactions())

    assert len(sales) == 2
    assert sales["Invoice"].tolist() == ["10001", "10002"]
    assert sales["Customer ID"].notna().all()
    assert sales["revenue"].tolist() == [20, 60]


def test_build_churn_dataset_creates_customer_level_labels():
    df = pd.DataFrame(
        {
            "Invoice": ["10001", "10002", "10003"],
            "StockCode": ["100", "101", "102"],
            "Quantity": [2, 3, 1],
            "InvoiceDate": ["2011-08-01", "2011-08-15", "2011-10-01"],
            "Price": [10, 20, 30],
            "Customer ID": [1, 1, 2],
            "Country": ["United Kingdom"] * 3,
        }
    )

    result = build_churn_dataset(df, cutoff="2011-09-01", horizon_days=60)

    assert len(result) == 1
    assert result.loc[0, "Customer ID"] == 1
    assert result.loc[0, "churn"] == 1
    assert result.loc[0, "frequency_orders"] == 2
    assert result.loc[0, "monetary_revenue"] == 80


def test_build_churn_dataset_rejects_non_positive_horizon():
    with pytest.raises(ValueError, match="horizon_days"):
        build_churn_dataset(sample_transactions(), horizon_days=0)
