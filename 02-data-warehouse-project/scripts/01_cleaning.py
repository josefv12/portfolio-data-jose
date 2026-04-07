"""
Proyecto 2 — Online Retail II
Paso 1: Limpieza de datos
Dataset: UCI Online Retail II (2009-2011)
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ──────────────────────────────────────────────
# RUTAS (relativas al proyecto, no al script)
# ──────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
RAW_DATA   = BASE_DIR / 'data' / 'raw' / 'online_retail_II.csv'
OUTPUT_DIR = BASE_DIR / 'data' / 'processed'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# 1. CARGA
# ──────────────────────────────────────────────
df = pd.read_csv(RAW_DATA, encoding='utf-8', on_bad_lines='skip')
df['Invoice'] = df['Invoice'].astype(str)
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

print(f"Filas originales: {len(df):,}")

# ──────────────────────────────────────────────
# 2. SEPARAR DEVOLUCIONES (facturas con prefijo C)
#    Las guardamos aparte — son datos válidos
#    para análisis de retornos, no para ventas.
# ──────────────────────────────────────────────
returns = df[df['Invoice'].str.startswith('C')].copy()
sales   = df[~df['Invoice'].str.startswith('C')].copy()

print(f"Devoluciones separadas: {len(returns):,}")
print(f"Ventas a limpiar:       {len(sales):,}")

# ──────────────────────────────────────────────
# 3. ELIMINAR STOCK CODES NO-PRODUCTO
#    POST, DOT, M, etc. son cargos de servicio,
#    no productos físicos del catálogo.
# ──────────────────────────────────────────────
non_product_codes = ['POST', 'DOT', 'M', 'C2', 'D', 'S', 'BANK CHARGES']
sales = sales[~sales['StockCode'].isin(non_product_codes)]
sales = sales[sales['StockCode'].str.match(r'^\d', na=False)]

# ──────────────────────────────────────────────
# 4. ELIMINAR PRECIOS Y CANTIDADES INVÁLIDOS
#    Price=0 → item sin precio asignado
#    Quantity<0 en ventas → error de registro
# ──────────────────────────────────────────────
sales = sales[sales['Price'] > 0]
sales = sales[sales['Quantity'] > 0]

# ──────────────────────────────────────────────
# 5. IMPUTAR DESCRIPTIONS NULAS
#    Buscamos la descripción más frecuente
#    para ese StockCode en el resto del dataset.
# ──────────────────────────────────────────────
desc_map = (
    sales.dropna(subset=['Description'])
         .groupby('StockCode')['Description']
         .agg(lambda x: x.mode().iloc[0])
)
sales['Description'] = sales['Description'].fillna(
    sales['StockCode'].map(desc_map)
)

# ──────────────────────────────────────────────
# 6. PEDIDOS SIN CLIENTE → FLAG, NO ELIMINAR
#    22.6% de las filas no tienen Customer ID.
#    Son pedidos "guest". Los marcamos para
#    excluirlos de análisis RFM, pero los
#    mantenemos para revenue total.
# ──────────────────────────────────────────────
sales['is_guest'] = sales['Customer ID'].isnull()

# ──────────────────────────────────────────────
# 7. ELIMINAR PAÍS "Unspecified"
# ──────────────────────────────────────────────
sales = sales[sales['Country'] != 'Unspecified']

# ──────────────────────────────────────────────
# 8. COLUMNAS NUEVAS ÚTILES
# ──────────────────────────────────────────────
sales['revenue'] = (sales['Quantity'] * sales['Price']).round(2)
sales['year']    = sales['InvoiceDate'].dt.year
sales['month']   = sales['InvoiceDate'].dt.month

# ──────────────────────────────────────────────
# 9. RENOMBRAR A snake_case (convención SQL)
# ──────────────────────────────────────────────
sales.rename(columns={
    'Invoice':     'invoice_no',
    'StockCode':   'stock_code',
    'Description': 'description',
    'Quantity':    'quantity',
    'InvoiceDate': 'invoice_date',
    'Price':       'unit_price',
    'Customer ID': 'customer_id',
    'Country':     'country',
}, inplace=True)

returns.rename(columns={
    'Invoice':     'invoice_no',
    'StockCode':   'stock_code',
    'Description': 'description',
    'Quantity':    'quantity',
    'InvoiceDate': 'invoice_date',
    'Price':       'unit_price',
    'Customer ID': 'customer_id',
    'Country':     'country',
}, inplace=True)

# ──────────────────────────────────────────────
# 10. GUARDAR
# ──────────────────────────────────────────────
sales.to_csv(OUTPUT_DIR / 'online_retail_clean.csv', index=False)
returns.to_csv(OUTPUT_DIR / 'online_retail_returns.csv', index=False)
# ──────────────────────────────────────────────
# REPORTE FINAL
# ──────────────────────────────────────────────
print("\n" + "="*45)
print("REPORTE DE LIMPIEZA")
print("="*45)
print(f"Filas limpias (ventas):     {len(sales):>10,}")
print(f"Devoluciones (separadas):   {len(returns):>10,}")
print(f"Filas eliminadas:           {len(df)-len(sales):>10,}  ({round((1-len(sales)/len(df))*100,1)}%)")
print(f"Clientes únicos (con ID):   {sales['customer_id'].dropna().nunique():>10,}")
print(f"Productos únicos:           {sales['stock_code'].nunique():>10,}")
print(f"Facturas únicas:            {sales['invoice_no'].nunique():>10,}")
print(f"Revenue total:              £{sales['revenue'].sum():>10,.0f}")
print(f"Período:                    2009-12-01 → 2011-12-09")
