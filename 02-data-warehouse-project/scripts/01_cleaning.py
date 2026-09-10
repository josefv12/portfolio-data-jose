"""Proyecto 2 — Online Retail II: limpieza y preparación de datos."""

from pathlib import Path
import sys

import pandas as pd

# Permite ejecutar este script directamente desde la carpeta del proyecto.
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from shared.retail.cleaning import clean_retail_data

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA = BASE_DIR / "data" / "raw" / "online_retail_II.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Load raw data, apply canonical cleaning rules, and save outputs."""
    df = pd.read_csv(RAW_DATA, encoding="utf-8", on_bad_lines="skip")

    print(f"Filas originales: {len(df):,}")

    sales, returns = clean_retail_data(df)

    print(f"Devoluciones separadas: {len(returns):,}")
    print(f"Ventas limpias:         {len(sales):,}")

    sales.to_csv(OUTPUT_DIR / "online_retail_clean.csv", index=False)
    returns.to_csv(OUTPUT_DIR / "online_retail_returns.csv", index=False)

    print("\n" + "=" * 45)
    print("REPORTE DE LIMPIEZA")
    print("=" * 45)
    print(f"Filas limpias (ventas):     {len(sales):>10,}")
    print(f"Devoluciones (separadas):   {len(returns):>10,}")
    print(
        f"Filas eliminadas:           {len(df)-len(sales):>10,}  "
        f"({round((1-len(sales)/len(df))*100,1)}%)"
    )
    print(f"Clientes únicos (con ID):   {sales['customer_id'].dropna().nunique():>10,}")
    print(f"Productos únicos:           {sales['stock_code'].nunique():>10,}")
    print(f"Facturas únicas:            {sales['invoice_no'].nunique():>10,}")
    print(f"Revenue total:              £{sales['revenue'].sum():>10,.0f}")
    print(
        "Período:                    "
        f"{sales['invoice_date'].min():%Y-%m-%d} → "
        f"{sales['invoice_date'].max():%Y-%m-%d}"
    )


if __name__ == "__main__":
    main()
