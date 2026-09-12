# 04 — Customer Churn Prediction

## Objetivo

Construir un modelo de clasificación para identificar clientes con alta probabilidad de dejar de comprar, a partir de su comportamiento histórico de compras.

El proyecto utiliza **Online Retail II**, el mismo conjunto transaccional utilizado en los proyectos de retail del portafolio.

---

## Enfoque

El dataset original contiene transacciones, no una variable `churn`. Por eso se construye una tabla a nivel cliente:

```text
Transacciones
     ↓
Limpieza
     ↓
Historial antes del corte
     ↓
Features por cliente
     ↓
Ventana futura de 90 días
     ↓
Target: churn
     ↓
Random Forest
```

### Definición de churn

Se utiliza el **10 de septiembre de 2011** como fecha de corte y una ventana de observación futura de **90 días**.

- **Churn = 1:** el cliente compró antes del corte y no volvió a comprar durante los 90 días siguientes.
- **Churn = 0:** el cliente volvió a comprar durante esa ventana.

Los clientes cercanos al final del dataset que no disponen de la ventana completa no se utilizan para etiquetar el modelo.

---

## Dataset de modelado

| Métrica | Resultado |
|---|---:|
| Clientes | 5,250 |
| Churn | 2,963 (56.4%) |
| No churn | 2,287 (43.6%) |
| Horizonte | 90 días |
| Fecha de corte | 2011-09-10 |

### Variables principales

- `recency_days`
- `frequency_orders`
- `monetary_revenue`
- `total_units`
- `active_months`
- `unique_products`
- `average_order_value`
- `avg_units_per_order`
- `country`

El identificador del cliente se conserva para trazabilidad, pero se excluye de las variables utilizadas por el modelo.

---

## Modelo

Se utiliza un **Random Forest Classifier** dentro de un pipeline de scikit-learn.

El pipeline realiza:

1. Imputación de valores numéricos.
2. Imputación y One-Hot Encoding de variables categóricas.
3. Entrenamiento del Random Forest.
4. Evaluación sobre un conjunto de prueba separado.

Se utiliza `random_state=42` para reproducibilidad y `class_weight="balanced"` para compensar el desbalance de clases.

---

## Resultados

| Métrica | Resultado |
|---|---:|
| ROC-AUC | **0.775** |
| PR-AUC | **0.780** |
| Precision — churn | **0.73** |
| Recall — churn | **0.80** |
| F1 — churn | **0.76** |
| Accuracy | **0.72** |

### Matriz de confusión

```text
              Pred 0    Pred 1
Real 0           281       176
Real 1           120       473
```

### Interpretación de negocio

El modelo alcanza un **recall de 80% para clientes churn**, por lo que identifica una proporción alta de los clientes que posteriormente dejaron de comprar dentro de la ventana definida.

Para un escenario de retención, este resultado puede utilizarse como punto de partida para priorizar clientes antes de invertir recursos en campañas o incentivos.

El modelo no debe interpretarse como una garantía de que un cliente abandonará, sino como una herramienta de **priorización de riesgo**.

---

## Reproducibilidad

El dataset transaccional original no se almacena en GitHub.

Generar el dataset de modelado:

```bash
cd 04-churn-prediction-ml
python src/make_dataset.py --input /ruta/online_retail_II.csv
```

Entrenar y evaluar:

```bash
python src/train.py
```

Los archivos generados localmente son:

```text
data/processed/churn.csv
models/churn_pipeline.joblib
reports/metrics.json
```

Estos artefactos están excluidos de Git mediante `.gitignore`.

---

## Stack

Python · Pandas · Scikit-learn · Random Forest · Joblib · GitHub Actions

---

**Dataset:** UCI Online Retail II  
**Proyecto anterior:** [03 — Executive Dashboard](../03-executive-dashboard)
