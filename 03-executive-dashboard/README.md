# 03 - Executive Dashboard

## Descripción General

Este proyecto consiste en un tablero interactivo diseñado para proporcionar a los ejecutivos una visión clara y en tiempo real de los indicadores clave de rendimiento (KPIs) del negocio. El dashboard está construido utilizando **Streamlit**, con soporte para análisis de datos y visualizaciones dinámicas.

### Enlace al Dashboard

Accede al tablero en línea: [Executive Dashboard](https://portfolio-data-jose-7kav7yepgv3how7vfbtywu.streamlit.app/)

---

## Características Principales

- **Comparativa de Revenue vs Target**: Visualización clara del rendimiento frente a los objetivos establecidos.
- **Top 5 Productos**: Identificación de los productos con mayor margen de contribución.
- **Mapa de Calor Regional**: Análisis de ventas por región para detectar patrones y anomalías.

---

## Estructura del Proyecto

- **`app.py`**: Archivo principal que ejecuta la aplicación Streamlit.
- **`data/processed/`**: Contiene los datasets procesados:
  - `online_retail_clean.csv`
  - `online_retail_returns.csv`
  - `sample_clean.csv`
- **`scripts/`**:
  - `create_sample.py`: Genera datos de muestra para pruebas.
  - `load_to_postgres.py`: Carga los datos procesados en una base de datos PostgreSQL.
- **`requirements.txt`**: Lista de dependencias necesarias para ejecutar el proyecto.

---

## Instalación y Configuración

1. Clona este repositorio:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd 03-executive-dashboard
   ```
2. Crea y activa un entorno virtual:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Configura las variables de entorno en `env.example` y renómbralo a `.env`.

---

## Uso

1. Ejecuta la aplicación:
   ```bash
   streamlit run app.py
   ```
2. Accede al dashboard en tu navegador en `http://localhost:8501`.

---

## Tecnologías Utilizadas

- **Streamlit**: Framework para construir aplicaciones web interactivas.
- **Pandas**: Manipulación y análisis de datos.
- **Plotly**: Visualizaciones interactivas.
- **SQLAlchemy**: Conexión y manejo de bases de datos.
- **PostgreSQL**: Base de datos relacional.

---

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o envía un pull request para sugerencias o mejoras.
