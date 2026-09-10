import pandas as pd

from shared.retail.metrics import (
    average_order_value,
    return_rate_pct,
    revenue_total,
    total_orders,
    unique_customers,
    units_sold,
)


def make_sales():
    return pd.DataFrame(
        {
            "invoice_no": ["1001", "1001", "1002", "1003"],
            "revenue": [10.0, 5.0, 20.0, 8.0],
            "quantity": [2, 1, 4, 2],
            "customer_id": [101, 101, 102, None],
            "is_guest": [False, False, False, True],
        }
    )


def test_commercial_metrics_include_guest_sales():
    sales = make_sales()

    assert revenue_total(sales) == 43.0
    assert total_orders(sales) == 3
    assert units_sold(sales) == 9
    assert average_order_value(sales) == 43.0 / 3


def test_customer_metric_excludes_guest_sales():
    assert unique_customers(make_sales()) == 2


def test_return_rate_uses_sold_plus_returned_units():
    sales = make_sales()
    returns = pd.DataFrame({"quantity": [-1, -1]})

    assert return_rate_pct(sales, returns) == 2 / 11 * 100
