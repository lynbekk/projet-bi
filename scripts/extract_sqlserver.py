import pandas as pd
from sqlalchemy import create_engine

server = r"localhost\SQLEXPRESS"  # Ton instance SQL
database = "Northwind"

# Connexion avec authentification Windows (la plus probable pour toi)
conn_str = f"mssql+pyodbc://@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"

engine = create_engine(conn_str)

# Test simple : lecture dans SQL Server
df = pd.read_sql("SELECT TOP 10 * FROM Products", engine)
print("\n Connexion réussie ! 🌟\n")
print(df)
