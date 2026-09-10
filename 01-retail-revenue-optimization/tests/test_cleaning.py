import pandas as pd
import pytest

from src.cleaning import clean_retail_data, validate_required_columns


def make_raw_data():
    return pd.DataFrame(
        {
            "Invoice": ["1001", "C1002", "1003", "1004", "1005", "1006", "1007"],
            "StockCode": ["10001", "10002", "POST", "ABC", "10003", "10004", "10005"],
            "Description": ["A", "B", "Postage", "Invalid", None, "D", "E"],
            "Quantity": [2, -1, 1, 1, 3, 0, 2],
            "InvoiceDate": pd.to_datetime(
                [
                    "2011-12-01",
                    "2011-12-01",
                    "2011-12-02",
                    "2011-12-02",
                    "2011-12-03",
                    "2011-12-03",
                    "2011-12-04",
                ]
            ),
            "Price": [5.0, 4.0, 1.0, 2.0, 3.0, 2.0, 2.5],
            "Customer ID": [12345, 12345, None, 12346, None, 12347, 12348],
            "Country": [
                "United Kingdom",
                "United Kingdom",
                "United Kingdom",
                "United Kingdom",
                "Unspecified",
                "United Kingdom",
                "United Kingdom",
            ],
        }
    )


def test_cleaning_keeps_valid_product_sales_and_guest_flag():
    sales, returns = clean_retail_data(make_raw_data())

    assert len(returns) == 1
    assert set(sales["invoice_no"]) == {"1001", "1007"}
    assert sales.loc[sales["invoice_no"] == "1001", "revenue"].iloc[0] == 10.0
    assert sales.loc[sales["invoice_no"] == "1007", "is_guest"].iloc[0] is False


def test_cleaning_excludes_non_product_and_invalid_sales():
    sales, _ = clean_retail_data(make_raw_data())

    assert "POST" not in sales["stock_code"].tolist()
    assert "10003" not in sales["stock_code"].tolist()
    assert "ABC" not in sales["stock_code"].tolist()
    assert all(sales["quantity"] > 0)
    assert all(sales["unit_price"] > 0)


def test_required_columns_validation():
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_required_columns(["Invoice", "Price"])
