import pandas as pd
import os

DATA_DIR = "data"

# Charger fact SQL existant
sql_fact_path = os.path.join(DATA_DIR, "fact_order.csv")
df_sql = pd.read_csv(sql_fact_path) if os.path.exists(sql_fact_path) else pd.DataFrame()

# Charger Access : Orders + Order_Details
orders_path = os.path.join(DATA_DIR, "Orders.csv")
details_path = os.path.join(DATA_DIR, "Order_Details.csv")

df_orders = pd.read_csv(orders_path)
df_details = pd.read_csv(details_path)

print("\n📌 Colonnes chargées :")
print("Orders:", list(df_orders.columns))
print("Order_Details:", list(df_details.columns))

# Fusion Access sur "Order ID"
df_acc = df_details.merge(df_orders, on="Order ID", how="left")

# Création du montant total : Quantity * Unit Price * (1 – Discount)
df_acc["Quantity"] = df_acc["Quantity"].astype(float)
df_acc["Unit Price"] = df_acc["Unit Price"].astype(float)
df_acc["Discount"] = df_acc["Discount"].astype(float)

df_acc["line_total"] = df_acc["Quantity"] * df_acc["Unit Price"] * (1 - df_acc["Discount"])

# Renommer pour correspondre au modèle SQL fact
df_acc = df_acc.rename(columns={
    "Order ID": "order_id",
    "Product ID": "product_key",
    "Customer ID": "customer_key",
    "Employee ID": "employee_key",
    "Shipper ID": "shipper_key",
    "Order Date": "order_date"
})

# Sélection des colonnes utiles
cols = [
    "order_id", "customer_key", "product_key", "employee_key", "shipper_key",
    "Quantity", "Unit Price", "Discount", "line_total", "order_date"
]

df_acc = df_acc[[c for c in cols if c in df_acc.columns]]

# Unification SQL + Access
frames = []
if not df_sql.empty:
    frames.append(df_sql)
frames.append(df_acc)

df_unified = pd.concat(frames, ignore_index=True, sort=False)

# Enregistrer
output_path = os.path.join(DATA_DIR, "fact_order_unified.csv")
df_unified.to_csv(output_path, index=False)

print("\n🎉 Fichier unifié généré !")
print("→", output_path)
