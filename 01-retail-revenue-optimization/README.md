Retail Revenue Optimization
Proyecto 1 de 4 — Análisis Exploratorio de Datos

Portafolio: portfolio-data-jose


🧩 El problema de negocio
Un e-commerce del Reino Unido (2009–2011) necesita entender su comportamiento de ventas para definir la estrategia del próximo año. Con más de 1 millón de transacciones reales, respondemos 5 preguntas críticas:

¿Los ingresos están creciendo? ¿Hay estacionalidad?
¿Cuánto dependemos del mercado británico?
¿Qué productos son los verdaderos motores del negocio?
¿Cuándo compra nuestra gente?
¿Estamos reteniendo clientes?


🔍 Hallazgos principales
Pregunta HallazgoImpacto
¿Crecimiento? Pico en Nov 2011 — £274K en un mes
Planificar inventario desde sep¿Dependencia UK?83% concentrado en UKExpandir Europa continental
¿Productos clave?Top 10 SKUs = motor del ingresoStock garantizado
¿Cuándo compran?Jueves y miércoles son los días peakActivar campañas Tue–Thu¿Retención?~96% de clientes son recurrentesPrograma de lealtad

📊 KPIs del dataset
MétricaValor💰 Ingresos totales£20.97 millones🧾 Órdenes~22,000+👤 Clientes únicos~5,800📦 SKUs únicos~4,600🗓️ PeríodoDic 2009 – Dic 2011

📁 Estructura
01-retail-revenue-optimization/
├── data/
│   └── online_retail_II.csv        # Dataset fuente (UCI ML Repository)
├── notebooks/
│   ├── retail_eda_notebook.ipynb   # Análisis completo con storytelling
│   ├── fig1_monthly_revenue.png
│   ├── fig2_countries.png
│   ├── fig3_products.png
│   ├── fig4_dayofweek.png
│   └── fig5_retention.png
└── README.md

🛠️ Stack técnico
Python 3 · Pandas · Matplotlib · Jupyter Notebook

🚀 Cómo ejecutar
bashcd 01-retail-revenue-optimization
pip install pandas matplotlib
jupyter notebook notebooks/retail_eda_notebook.ipynb

Dataset: Online Retail II — UCI ML Repository


Jose Fernández · LinkedIn · GitHub