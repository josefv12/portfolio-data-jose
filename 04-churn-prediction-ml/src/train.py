"""Train and evaluate a leakage-safe churn classification pipeline."""

from pathlib import Path
import argparse
import json

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.data import TARGET, load_dataset
from src.features import prepare_features

RANDOM_STATE = 42


def build_pipeline(X: pd.DataFrame) -> Pipeline:
    """Build preprocessing and model steps without fitting on held-out data."""
    numeric = X.select_dtypes(include="number").columns.tolist()
    categorical = X.select_dtypes(exclude="number").columns.tolist()

    if not numeric and not categorical:
        raise ValueError("At least one predictor column is required.")

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


def evaluate_predictions(y_true: pd.Series, probabilities, predictions) -> dict:
    """Return business-relevant classification metrics."""
    matrix = confusion_matrix(y_true, predictions, labels=[0, 1])
    report = classification_report(y_true, predictions, output_dict=True, zero_division=0)

    return {
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "pr_auc": float(average_precision_score(y_true, probabilities)),
        "precision": float(report["1"]["precision"]),
        "recall": float(report["1"]["recall"]),
        "f1": float(report["1"]["f1-score"]),
        "confusion_matrix": matrix.tolist(),
        "classification_report": report,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the churn model.")
    parser.add_argument("--data", default="data/processed/churn.csv")
    parser.add_argument("--model-out", default="models/churn_pipeline.joblib")
    parser.add_argument("--metrics-out", default="reports/metrics.json")
    args = parser.parse_args()

    df = load_dataset(args.data)
    X = prepare_features(df)
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
    metrics = evaluate_predictions(y_test, probabilities, predictions)
    metrics.update({"test_rows": int(len(X_test)), "random_state": RANDOM_STATE})

    model_path = Path(args.model_out)
    metrics_path = Path(args.metrics_out)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"PR-AUC:   {metrics['pr_auc']:.4f}")
    print(f"Recall:   {metrics['recall']:.4f}")
    print(f"Model saved to: {model_path}")
    print(f"Metrics saved to: {metrics_path}")


if __name__ == "__main__":
    main()
