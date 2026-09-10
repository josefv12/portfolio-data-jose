# Dataset contract

## Objective

Transform the transaction-level **Online Retail II** dataset into one row per identified customer and predict whether that customer will become inactive during a future 90-day period.

## Source data

- **Dataset:** UCI Online Retail II
- **Raw rows:** 1,067,371 transactions
- **Period:** December 2009 – December 2011
- **Target dataset:** customer-level behavioral features
- **Raw dataset:** intentionally excluded from version control

## Churn definition

The modeling cutoff is **2011-09-10**. Customer behavior observed before the cutoff is used to build the predictors. A customer is labeled:

- `churn = 1`: no valid purchase during the following 90 days.
- `churn = 0`: at least one valid purchase during the following 90 days.

Customers are included only when they have purchase history before the cutoff and therefore have the complete 90-day future window available for labeling.

This definition avoids labeling customers near the end of the source dataset when their future behavior cannot be observed completely.

## Cleaning rules

The dataset builder follows the portfolio's retail cleaning contract:

- exclude cancelled invoices (`Invoice` beginning with `C`);
- exclude non-product stock codes (`POST`, `DOT`, `M`, `C2`, `D`, `S`, `BANK CHARGES`);
- keep product stock codes beginning with a digit;
- require `Quantity > 0` and `Price > 0`;
- exclude `Country = Unspecified`;
- exclude transactions without an identified `Customer ID` because churn is modeled at customer level.

## Features

The customer-level dataset contains behavioral variables calculated only from transactions before the cutoff:

| Feature | Meaning |
|---|---|
| `recency_days` | Days since the customer's last purchase before cutoff |
| `frequency_orders` | Number of unique orders |
| `monetary_revenue` | Total revenue generated |
| `total_units` | Total units purchased |
| `active_months` | Number of months with at least one purchase |
| `unique_products` | Number of distinct products purchased |
| `average_order_value` | Revenue divided by number of orders |
| `avg_units_per_order` | Average units purchased per order |
| `country` | Customer's country |

Customer identifiers are retained only to trace records and are removed before model training.

## Leakage rules

The feature set must contain information available **before the churn decision**. The following are not used as predictors:

- the churn target;
- customer identifiers;
- future transactions;
- post-cutoff behavior;
- variables directly derived from the future churn label;
- purchase dates that reveal the target period.

In particular, `last_purchase_date` is not stored as a model feature because recency is already represented by `recency_days`.

## Validation

Before training, validate:

- the target exists and is not empty;
- the target contains exactly two classes;
- missing values are handled inside the modeling pipeline;
- categorical encoding is learned only from the training split;
- the test set remains untouched until final evaluation.

## Reproducibility

The dataset builder is implemented in `src/make_dataset.py` and uses a fixed cutoff (`2011-09-10`) and a 90-day prediction horizon by default. Training uses a fixed random seed (`42`).

Example:

```bash
python src/make_dataset.py \
  --input /path/to/online_retail_II.csv \
  --output data/processed/churn.csv
```

The generated dataset is ignored by Git and should not be committed.

## Current status

The customer-level dataset construction pipeline is implemented. The next step is to generate the dataset locally, run the training pipeline, and report the resulting model metrics. No model performance is claimed until that execution is completed.
