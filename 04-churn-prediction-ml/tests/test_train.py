import pandas as pd
from sklearn.pipeline import Pipeline

from src.train import build_pipeline


def test_build_pipeline_handles_numeric_and_categorical_features():
    X = pd.DataFrame(
        {
            "tenure_months": [3, 12, 24, 6],
            "plan": ["basic", "premium", "premium", "basic"],
        }
    )

    pipeline = build_pipeline(X)
    pipeline.fit(X, [1, 0, 0, 1])

    predictions = pipeline.predict(X)

    assert isinstance(pipeline, Pipeline)
    assert len(predictions) == len(X)
    assert set(predictions).issubset({0, 1})
