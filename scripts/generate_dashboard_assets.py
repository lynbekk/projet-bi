import pandas as pd
import sqlite3
import os
import matplotlib.pyplot as plt

# Connexion Data Warehouse
conn = sqlite3.connect("northwind_dwh.db")
fact = pd.read_sql("SELECT * FROM fact_order", conn)
time = pd.read_sql("SELECT * FROM dim_time", conn)
cust = pd.read_sql("SELECT * FROM dim_customer", conn)
prod = pd.read_sql("SELECT * FROM dim_product", conn)

os.makedirs("figures", exist_ok=True)

# Join pour dashboard
df = fact.merge(time, on="time_key").merge(cust,on="customer_key").merge(prod,on="product_key")

# KPI
CA_TOTAL = df.line_total.sum()
TOP_CLIENT = df.groupby("CompanyName")["line_total"].sum().sort_values(ascending=False).head(1).index[0]
MEAN_DISCOUNT = df.Discount_detail.mean()*100

with open("kpis.txt","w") as f:
    f.write(f"CA total = {CA_TOTAL:,.2f} $\n")
    f.write(f"Meilleur client = {TOP_CLIENT}\n")
    f.write(f"Remise moyenne = {MEAN_DISCOUNT:.2f} %\n")

# Graphiques
df.groupby("year")["line_total"].sum().plot(kind="bar")
plt.title("Chiffre d'affaire par année")
plt.savefig("figures/ca_par_annee.png")
plt.close()

df.groupby("ProductName")["line_total"].sum().sort_values(ascending=False).head(10).plot(kind="bar")
plt.title("Top 10 Produits")
plt.savefig("figures/top_produits.png")
plt.close()

print("📊 KPI + Graphiques générés dans /figures")
