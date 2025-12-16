import pandas as pd
from sqlalchemy import create_engine

# Подключение к базе данных PostgreSQL
engine = create_engine('postgresql://postgres:5252@localhost:5432/practik_db')

# Загружаем CSV в PostgreSQL
df_product_types = pd.read_csv('out_csv/product_types.csv')
df_product_types.to_sql('product_types', engine, if_exists='append', index=False)

df_material_types = pd.read_csv('out_csv/material_types.csv')
df_material_types.to_sql('material_types', engine, if_exists='append', index=False)

df_workshops = pd.read_csv('out_csv/workshops.csv')
df_workshops.to_sql('workshops', engine, if_exists='append', index=False)

df_products = pd.read_csv('out_csv/products.csv')
df_products.to_sql('products', engine, if_exists='append', index=False)

df_product_workshops = pd.read_csv('out_csv/product_workshops.csv')
df_product_workshops.to_sql('product_workshops', engine, if_exists='append', index=False)

print("Данные успешно импортированы в базу данных PostgreSQL!")
