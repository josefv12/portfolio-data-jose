# Executive Dashboard — Online Retail II

Una tienda de regalos UK con £20M en revenue y operaciones en 43 países
no tenía forma de monitorear sus métricas clave en tiempo real.
Los datos existían — pero estaban atrapados en CSVs.

Este proyecto construye un dashboard interactivo con Streamlit que convierte
esos datos en decisiones: filtrable por año y país, con KPIs en tiempo real
y análisis de clientes, productos y devoluciones.

**[Ver dashboard en vivo](https://portfolio-data-jose-7kav7yepgv3how7vfbtywu.streamlit.app)**

---

## KPIs del negocio (dataset completo)

| Métrica              | Valor                       |
| -------------------- | --------------------------- |
| Revenue total        | £20,098,059                 |
| Pedidos únicos       | 39,492                      |
| Clientes registrados | 5,846                       |
| Ticket promedio      | £509                        |
| Return rate          | 1.85% de transacciones      |
| Mes pico             | Noviembre 2011 — £1,456,776 |

---

## Hallazgos clave

**El 86.7% del revenue viene de clientes registrados** — pero el 13.3% restante
son pedidos guest sin Customer ID. Eso es £2.67M que no se puede atribuir
a ningún cliente para retención o remarketing.

**EIRE, Netherlands y Germany** son los mercados internacionales más rentables,
con £628K, £549K y £388K respectivamente — muy por encima del resto de Europa.

**Noviembre 2011** fue el mes pico con £1.45M — casi 3x el promedio mensual.
El dashboard permite ver exactamente qué productos y países impulsaron ese pico.

---

## Stack

Python · Streamlit · Plotly · pandas · PostgreSQL · Docker · SQLAlchemy

---

## Arquitectura

```
PostgreSQL (proyecto 2)          CSV fallback (Streamlit Cloud)
        │                                    │
        └──────────── app.py ────────────────┘
                          │
                    Streamlit Cloud
                          │
              ┌───────────┴───────────┐
           Sidebar                  Tabs
        (filtros año/país)   Revenue · Products
                             Customers · Returns
```

El dashboard detecta automáticamente si hay una base de datos disponible
(`DATABASE_URL` en variables de entorno). Si no, usa los CSVs de muestra.
Esto permite correrlo localmente con PostgreSQL y en Streamlit Cloud sin DB.

---

## Vistas del dashboard

**Revenue Trends** — serie temporal mensual con rolling average de 3 meses,
donut de revenue por año y heatmap mes × año.

**Products** — top 10 por revenue y por unidades, curva Pareto con corte
del 80% y scatter precio vs volumen vendido.

**Customers** — revenue guest vs registrado, top 10 clientes, nuevos clientes
por mes e histograma de distribución de revenue por cliente.

**Returns** — KPIs de devoluciones, países y productos con más retornos
y tendencia mensual de volumen de devoluciones.

---

## Cómo correrlo localmente

```bash
# 1. Clonar el repo
git clone https://github.com/josefv12/portfolio-data-jose
cd portfolio-data-jose/03-executive-dashboard

# 2. Instalar dependencias
pip install -r requirements.txt

# 3a. Con PostgreSQL (datos completos)
cp env.example .env
# Editar .env con tu DATABASE_URL
python scripts/load_to_postgres.py
streamlit run app.py

# 3b. Sin PostgreSQL (usa sample automáticamente)
streamlit run app.py
```

> El dataset completo se descarga desde
> [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
> y se coloca en `data/processed/` tras correr el proyecto 2.

---

## Estructura

```
03-executive-dashboard/
├── app.py                          ← dashboard principal
├── scripts/
│   ├── create_sample.py            ← genera muestra para Streamlit Cloud
│   └── load_to_postgres.py         ← carga datos completos a PostgreSQL
├── data/
│   └── processed/
│       ├── sample_clean.csv        ← 5,000 filas (Streamlit Cloud fallback)
│       └── sample_returns.csv      ← 250 devoluciones proporcionales
├── requirements.txt
└── env.example
```

---

**Dataset**: UCI Online Retail II · 1,067,371 transacciones · 2009–2011
**Proyecto anterior**: [02 — Data Warehouse](../02-data-warehouse-project)
