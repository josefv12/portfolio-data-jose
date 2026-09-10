import pandas as pd
import pytest

from src.data import TARGET, load_dataset


def test_load_dataset_returns_dataframe(tmp_path):
    path = tmp_path / "churn.csv"
    pd.DataFrame({"customer_id": [1, 2], TARGET: [0, 1]}).to_csv(path, index=False)

    df = load_dataset(path)

    assert list(df.columns) == ["customer_id", TARGET]
    assert len(df) == 2


def test_load_dataset_requires_target(tmp_path):
    path = tmp_path / "churn.csv"
    pd.DataFrame({"customer_id": [1, 2]}).to_csv(path, index=False)

    with pytest.raises(ValueError, match="Target column"):
        load_dataset(path)


def test_load_dataset_rejects_empty_dataset(tmp_path):
    path = tmp_path / "churn.csv"
    pd.DataFrame(columns=["customer_id", TARGET]).to_csv(path, index=False)

    with pytest.raises(ValueError, match="empty"):
        load_dataset(path)


def test_load_dataset_requires_existing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="Dataset not found"):
        load_dataset(tmp_path / "missing.csv")
