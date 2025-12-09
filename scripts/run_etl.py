import os

print("\n=== 🚀 ETL BI NORTHWIND START ===")

os.system("python extract_sqlserver.py")
os.system("python transform.py")
os.system("python load_dwh.py")

print("\n=== 🎉 ETL COMPLET & DWH DISPONIBLE ===\n")
