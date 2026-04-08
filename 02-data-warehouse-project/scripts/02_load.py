"""
Proyecto 2 — Online Retail II
Paso 2: Carga a PostgreSQL
Archivo: scripts/02_load.py
"""

import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
import time

# ──────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "retail_db",
    "user":     "postgres",
    "password": "admin123",
    "schema":   "retail",
}

BASE_DIR    = Path(__file__).resolve().parent.parent
CLEAN_CSV   = BASE_DIR / "data" / "processed" / "online_retail_clean.csv"
RETURNS_CSV = BASE_DIR / "data" / "processed" / "online_retail_returns.csv"

# ──────────────────────────────────────────────
# CONEXIÓN
# ──────────────────────────────────────────────
def get_engine():
    url = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    )
    return create_engine(url, echo=False)


def log(msg):
    print(f"  {msg}")


# ──────────────────────────────────────────────
# LIMPIAR TABLAS
# ──────────────────────────────────────────────
def truncate_tables(engine, schema):
    print("\n[0/6] Limpiando tablas (TRUNCATE)...")

    tables = ["returns", "invoice_items", "invoices", "products", "customers"]

    with engine.connect() as conn:
        for t in tables:
            conn.execute(text(f"TRUNCATE TABLE {schema}.{t} RESTART IDENTITY CASCADE"))
        conn.commit()

    print("  Tablas limpias ✔")


# ──────────────────────────────────────────────
# CARGA POR CHUNKS
# ──────────────────────────────────────────────
def load_table(df, table, engine, schema, chunksize=1000):
    total = len(df)
    loaded = 0
    start = time.time()

    for chunk in range(0, total, chunksize):
        df.iloc[chunk:chunk + chunksize].to_sql(
            name=table,
            con=engine,
            schema=schema,
            if_exists="append",
            index=False,
            method="multi",
        )
        loaded += min(chunksize, total - chunk)
        pct = round(loaded / total * 100)
        print(f"\r    {table}: {loaded:,}/{total:,} filas ({pct}%)", end="", flush=True)

    elapsed = round(time.time() - start, 1)
    print(f"\r    {table}: {total:,} filas cargadas en {elapsed}s          ")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    print("\n" + "="*50)
    print("CARGA A POSTGRESQL — Online Retail II")
    print("="*50)

    engine = get_engine()
    schema = DB_CONFIG["schema"]

    # limpiar tablas
    truncate_tables(engine, schema)

    # ── LEER CSVs ──────────────────────────────
    print("\n[1/6] Leyendo CSVs...")
    sales = pd.read_csv(CLEAN_CSV, parse_dates=["invoice_date"])
    returns = pd.read_csv(RETURNS_CSV, parse_dates=["invoice_date"])

    sales = sales.dropna(subset=["invoice_no", "stock_code"])

    log(f"Ventas:       {len(sales):,} filas")
    log(f"Devoluciones: {len(returns):,} filas")

    # ── CUSTOMERS ──────────────────────────────
    print("\n[2/6] Cargando customers...")

    # Clientes registrados desde ventas
    registered_sales = (
        sales[~sales["is_guest"]][["customer_id", "country"]]
        .dropna(subset=["customer_id"])
        .copy()
    )

    # ✅ Clientes que aparecen SOLO en returns (huérfanos)
    # Son clientes reales cuyas ventas fueron filtradas en el paso de limpieza.
    # Se incluyen con first_purchase / last_purchase = NULL.
    registered_returns = (
        returns[
            returns["customer_id"].notna() &
            (returns["customer_id"] != 0)
        ][["customer_id", "country"]]
        .copy()
    )

    # Unir ambas fuentes antes de deduplicar
    registered = pd.concat([registered_sales, registered_returns], ignore_index=True)
    registered["customer_id"] = registered["customer_id"].astype(int)

    # Fechas de primera y última compra (solo desde ventas)
    dates = (
        sales[~sales["is_guest"]]
        .groupby("customer_id")["invoice_date"]
        .agg(first_purchase="min", last_purchase="max")
        .reset_index()
    )
    dates["customer_id"] = dates["customer_id"].astype(int)

    # Left join: los huérfanos de returns quedan con first/last_purchase = NaT → NULL
    customers = (
        registered.drop_duplicates("customer_id")
        .merge(dates, on="customer_id", how="left")
    )
    customers["is_guest"] = False

    # Cliente guest especial
    guest = pd.DataFrame([{
        "customer_id": 0,
        "country": "Unknown",
        "first_purchase": None,
        "last_purchase": None,
        "is_guest": True
    }])

    customers = pd.concat([customers, guest], ignore_index=True)

    # Diagnóstico
    orphans = customers[customers["first_purchase"].isna() & ~customers["is_guest"]]
    log(f"Clientes registrados con ventas:    {len(customers) - len(orphans) - 1:,}")
    log(f"Clientes sin ventas (solo returns): {len(orphans):,}  ← huérfanos incluidos")
    log(f"Total customers (+ guest):          {len(customers):,}")

    load_table(customers, "customers", engine, schema)

    # ── PRODUCTS ──────────────────────────────
    print("\n[3/6] Cargando products...")

    all_data = pd.concat([
        sales[["stock_code", "unit_price", "description"]],
        returns[["stock_code", "unit_price"]].assign(description=None)
    ], ignore_index=True)

    prices = (
        all_data.groupby("stock_code")["unit_price"]
        .median()
        .reset_index()
    )

    descriptions = (
        all_data.dropna(subset=["description"])
        .groupby("stock_code")["description"]
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)
        .reset_index()
    )

    products = prices.merge(descriptions, on="stock_code", how="left")

    load_table(products, "products", engine, schema)

    # ── INVOICES ──────────────────────────────
    print("\n[4/6] Cargando invoices...")

    invoices = (
        sales[["invoice_no", "customer_id", "country",
               "invoice_date", "year", "month", "is_guest"]]
        .drop_duplicates("invoice_no")
        .copy()
    )

    invoices["customer_id"] = invoices["customer_id"].fillna(0).astype(int)

    invoices = invoices[
        (invoices["customer_id"] == 0) |
        (invoices["customer_id"].isin(customers["customer_id"]))
    ]

    load_table(invoices, "invoices", engine, schema)

    # ── INVOICE_ITEMS ──────────────────────────
    print("\n[5/6] Cargando invoice_items...")

    valid_invoices = invoices["invoice_no"].unique()

    items = sales[
        sales["invoice_no"].isin(valid_invoices)
    ][["invoice_no", "stock_code", "quantity", "unit_price"]].copy()

    load_table(items, "invoice_items", engine, schema)

    # ── RETURNS ────────────────────────────────
    print("\n[6/6] Cargando returns...")

    valid_products  = products["stock_code"].unique()
    valid_customers = set(customers["customer_id"].unique())

    ret = returns[
        returns["stock_code"].isin(valid_products)
    ].copy()

    ret = ret[[
        "invoice_no",
        "customer_id",
        "stock_code",
        "country",
        "quantity",
        "unit_price",
        "invoice_date"
    ]]

    ret["quantity"]    = ret["quantity"].abs()
    ret["customer_id"] = ret["customer_id"].fillna(0).astype(int)

    # Seguridad: cualquier ID que todavía no exista → guest
    orphan_mask = ~ret["customer_id"].isin(valid_customers)
    if orphan_mask.any():
        log(f"⚠ {orphan_mask.sum()} filas reasignadas a guest (customer_id=0)")
        ret.loc[orphan_mask, "customer_id"] = 0

    ret = ret.drop(columns=["description"], errors="ignore")

    load_table(ret, "returns", engine, schema)

    # ── VERIFICACIÓN ───────────────────────────
    print("\n" + "="*50)
    print("VERIFICACIÓN DE CARGA")
    print("="*50)

    tables = ["customers", "products", "invoices", "invoice_items", "returns"]

    with engine.connect() as conn:
        for t in tables:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM {schema}.{t}")
            )
            count = result.scalar()
            print(f"  {t:<20} {count:>10,} filas")

    print("\nCarga completada ✔")


if __name__ == "__main__":
    main()