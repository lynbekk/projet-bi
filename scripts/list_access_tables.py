import pyodbc

DB_PATH = r"C:\Users\hp\OneDrive\Bureau\projet-BI\data\4476c464-0d07-4a3a-a0a3-b8de44a8d5bd.accdb"

conn_str = (
    r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
    f"DBQ={DB_PATH};"
)

conn = pyodbc.connect(conn_str)

cursor = conn.cursor()

# Liste toutes les tables Access
tables = cursor.tables(tableType='TABLE')

print("📌 Tables trouvées dans votre fichier Access :")
for table in tables:
    print(" -", table.table_name)

conn.close()
