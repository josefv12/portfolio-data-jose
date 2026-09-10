# Dataset contract

## Objective

The project predicts whether a customer will churn. The modeling dataset must contain one row per customer and a binary target named `churn`.

## Required contract

| Column | Requirement |
|---|---|
| `churn` | Required binary target (`0/1`, `False/True`, or equivalent values that are explicitly mapped before training) |
| Customer identifier | Optional; identifiers must not be used as predictive features |
| Predictors | Numeric and/or categorical customer attributes available before the churn decision |

## Leakage rules

The feature set must exclude information that would only become known after churn or after the retention decision, including cancellation timestamps, post-churn status fields, recovery outcomes, or target-derived variables.

## Validation

Before training, validate:

- the target exists and is not empty;
- the target contains exactly two classes;
- missing values are handled inside the modeling pipeline;
- categorical encoding is learned only from the training split;
- the test set remains untouched until final evaluation.

## Reproducibility

Training uses a fixed random seed (`42`). Raw/private datasets are intentionally excluded from version control. Once a public dataset is selected, its source, license, row count, feature definitions, and exact preprocessing decisions should be documented here.

## Current status

The repository contains the reusable training pipeline and tests, but **no real churn dataset has been committed yet**. Model metrics must not be reported until the dataset is supplied and the complete pipeline is executed.
