import pyodbc
import pandas as pd
import os

# ====== CONFIG ======
db_path = r"C:\Users\hp\Downloads\Northwind 2012 (1).accdb"  # adapte si besoin
output_dir = "../data_access"

# ====== CRÉATION DOSSIER ======
os.makedirs(output_dir, exist_ok=True)

# ====== CONNEXION ACCESS ======
conn_str = (
    r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
    rf"DBQ={db_path};"
)

try:
    conn = pyodbc.connect(conn_str)
    print("✅ Connexion réussie à Access !")

    cursor = conn.cursor()

    # récupérer uniquement les tables utilisateur
    tables = [t.table_name for t in cursor.tables() if t.table_type == "TABLE"]

    print("\n📌 Tables détectées :")
    for t in tables:
        print(" -", t)

    print("\n📤 Extraction en cours...\n")

    # extraire chaque table
    for table in tables:
        try:
            df = pd.read_sql(f"SELECT * FROM [{table}]", conn)
            csv_path = f"{output_dir}/{table.replace(' ', '_')}.csv"
            df.to_csv(csv_path, index=False, encoding="utf-8")
            print(f"   ✔ {table}  →  {csv_path}")
        except Exception as e:
            print(f"   ❌ Erreur extraction {table} :", e)

    print("\n🎉 Extraction terminée ! Les fichiers sont dans :", output_dir)

except Exception as e:
    print("❌ Erreur de connexion :", e)
