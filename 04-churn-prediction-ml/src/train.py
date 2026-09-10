"""Train and evaluate a leakage-safe churn classification pipeline."""

from pathlib import Path
import argparse
import json

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from data import TARGET, load_dataset

RANDOM_STATE = 42


def build_pipeline(X: pd.DataFrame) -> Pipeline:
    numeric = X.select_dtypes(include="number").columns.tolist()
    categorical = X.select_dtypes(exclude="number").columns.tolist()

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), numeric),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ],
        remainder="drop",
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=RANDOM_STATE,
        class_weight="balanced",
        n_jobs=-1,
    )
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the churn model.")
    parser.add_argument("--data", default="data/processed/churn.csv")
    parser.add_argument("--model-out", default="models/churn_pipeline.joblib")
    parser.add_argument("--metrics-out", default="reports/metrics.json")
    args = parser.parse_args()

    df = load_dataset(args.data)
    X = df.drop(columns=[TARGET])
    y = df[TARGET]

    if y.nunique() != 2:
        raise ValueError("Churn target must contain exactly two classes.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    pipeline = build_pipeline(X_train)
    pipeline.fit(X_train, y_train)

    probabilities = pipeline.predict_proba(X_test)[:, 1]
    predictions = pipeline.predict(X_test)
    metrics = {
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "classification_report": classification_report(
            y_test, predictions, output_dict=True
        ),
        "test_rows": int(len(X_test)),
        "random_state": RANDOM_STATE,
    }

    model_path = Path(args.model_out)
    metrics_path = Path(args.metrics_out)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"Model saved to: {model_path}")
    print(f"Metrics saved to: {metrics_path}")


if __name__ == "__main__":
    main()
