# 📊 Proyecto: Almacén de Datos para Inteligencia de Ingresos

## Introducción

En un mundo donde los datos son el nuevo petróleo, este proyecto se centra en la creación de un almacén de datos (Data Warehouse) optimizado para la analítica empresarial. El objetivo principal es transformar datos crudos en información valiosa que impulse decisiones estratégicas basadas en datos.

## Objetivo del Proyecto

Diseñar y construir un almacén de datos relacional que permita a las empresas de retail:

- Identificar a sus mejores clientes y productos más rentables.
- Detectar riesgos de pérdida de clientes (churn).
- Generar reportes y análisis clave para la toma de decisiones.

## Arquitectura del Proyecto

### Modelo Estrella

El diseño del almacén de datos sigue un modelo estrella, ideal para consultas analíticas rápidas y eficientes. Este modelo incluye:

- **Tablas de Hechos**:
  - Ventas
  - Transacciones
- **Tablas de Dimensiones**:
  - Productos
  - Tiempo
  - Clientes
  - Geografía

### Proceso ETL (Extracción, Transformación y Carga)

El flujo de datos se gestiona mediante un proceso ETL robusto:

1. **Extracción**: Recolección de datos desde múltiples fuentes.
2. **Transformación**: Limpieza, normalización y enriquecimiento de datos utilizando Python y SQL.
3. **Carga**: Inserción de datos en el almacén optimizado para consultas analíticas.

## Componentes del Proyecto

### 1. Datos

- **Fuente Cruda**: `data/raw/online_retail_II.csv`
- **Datos Procesados**:
  - `data/processed/online_retail_clean.csv`
  - `data/processed/online_retail_returns.csv`

### 2. Scripts

- `scripts/01_cleaning.py`: Limpieza y preprocesamiento de datos.
- `scripts/02_load.py`: Carga de datos en el almacén.
- `scripts/03_visualizations.py`: Generación de visualizaciones clave.

### 3. SQL

- `sql/01_schema.sql`: Definición del esquema del almacén.
- `sql/02_queries.sql`: Consultas analíticas para KPIs.
- `sql/03_views.sql`: Creación de vistas optimizadas.

### 4. Notebooks

Actualmente, la carpeta de notebooks está vacía, pero está preparada para análisis exploratorios y documentación adicional.

## Impacto Empresarial

Este proyecto permite a las empresas:

- **Optimizar ingresos**: Identificar productos y clientes más rentables.
- **Reducir churn**: Detectar clientes en riesgo de abandono.
- **Tomar decisiones informadas**: Basadas en datos confiables y accesibles.

## Herramientas y Tecnologías

- **Lenguajes**: Python, SQL
- **Bases de Datos**: PostgreSQL (o similar)
- **Bibliotecas**: Pandas, SQLAlchemy, Matplotlib
- **Metodologías**: ETL, Modelado Dimensional
