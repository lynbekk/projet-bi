import pyodbc

db_path = r"C:\Users\hp\Downloads\Northwind 2012 (1).accdb"  # change si besoin

conn_str = (
    r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
    rf"DBQ={db_path};"
)

try:
    conn = pyodbc.connect(conn_str)
    print("✅ Connexion réussie à Access")

    cursor = conn.cursor()

    # Récupérer uniquement les vraies tables (type=1 = user tables)
    tables = cursor.tables()
    print("\n📌 Tables trouvées :")
    for table in tables:
        if table.table_type == "TABLE":
            print(" -", table.table_name)

except Exception as e:
    print("❌ Erreur :", e)
