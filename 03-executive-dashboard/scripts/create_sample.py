import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ruta original (archivo grande)
input_path = os.path.join(BASE_DIR, "data/processed/online_retail_clean.csv")

# Ruta salida (archivo pequeño)
output_path = os.path.join(BASE_DIR, "data/processed/sample_clean.csv")

# Cargar
df = pd.read_csv(input_path)

# Reducir tamaño
df_sample = df.sample(5000, random_state=42)

# Guardar
df_sample.to_csv(output_path, index=False)

print("✅ Sample creado correctamente")