import pandas as pd
import pytest

from src.features import prepare_features


def test_prepare_features_removes_target_and_identifier_columns():
    df = pd.DataFrame(
        {
            "customer_id": [1, 2],
            "tenure_months": [4, 18],
            "plan": ["basic", "premium"],
            "churn": [1, 0],
        }
    )

    features = prepare_features(df)

    assert list(features.columns) == ["tenure_months", "plan"]


def test_prepare_features_requires_target():
    df = pd.DataFrame({"customer_id": [1, 2], "tenure_months": [4, 18]})

    with pytest.raises(ValueError, match="Target column"):
        prepare_features(df)
