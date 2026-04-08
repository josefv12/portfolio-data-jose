"""
scripts/load_to_postgres.py
─────────────────────────────────────────────────────────────────────────────
Loads the clean CSVs into PostgreSQL.
Run once before launching the dashboard.

Usage:
    python scripts/load_to_postgres.py

Requires:
    DATABASE_URL in .env or environment variable
    e.g. DATABASE_URL=postgresql://postgres:postgres@localhost:5432/online_retail
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/online_retail"
)

CLEAN_CSV   = "data/processed/online_retail_clean.csv"
RETURNS_CSV = "data/processed/online_retail_returns.csv"


def main():
    print("🔌 Connecting to PostgreSQL...")
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Connection OK")

    # ── Load clean transactions ────────────────────────────────────────────────
    print(f"\n📂 Reading {CLEAN_CSV}...")
    df = pd.read_csv(CLEAN_CSV)
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    print(f"   {len(df):,} rows loaded")

    print("⬆️  Writing to PostgreSQL table: online_retail_clean ...")
    df.to_sql(
        "online_retail_clean",
        engine,
        if_exists="replace",   # drop & recreate on each run
        index=False,
        chunksize=10_000,
        method="multi",
    )
    print("   Done.")

    # ── Load returns ────────────────────────────────────────────────────────────
    print(f"\n📂 Reading {RETURNS_CSV}...")
    ret = pd.read_csv(RETURNS_CSV)
    ret["invoice_date"] = pd.to_datetime(ret["invoice_date"])
    print(f"   {len(ret):,} rows loaded")

    print("⬆️  Writing to PostgreSQL table: online_retail_returns ...")
    ret.to_sql(
        "online_retail_returns",
        engine,
        if_exists="replace",
        index=False,
        chunksize=10_000,
        method="multi",
    )
    print("   Done.")

    # ── Verify ─────────────────────────────────────────────────────────────────
    with engine.connect() as conn:
        n_clean   = conn.execute(text("SELECT COUNT(*) FROM online_retail_clean")).scalar()
        n_returns = conn.execute(text("SELECT COUNT(*) FROM online_retail_returns")).scalar()

    print(f"\n✅ online_retail_clean   → {n_clean:,} rows")
    print(f"✅ online_retail_returns → {n_returns:,} rows")
    print("\n🎉 Data loaded successfully. You can now run: streamlit run app.py")


if __name__ == "__main__":
    main()
