import pandas as pd
from sqlalchemy import create_engine

# ===================== CONNEXION =====================
server = r"localhost\SQLEXPRESS"
database = "Northwind"
conn_str = f"mssql+pyodbc://@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(conn_str)

print("\n📡 Connexion SQL OK — Début TRANSFORMATION\n")

# ===================== EXTRACTION =====================
orders = pd.read_sql("SELECT * FROM Orders", engine)
order_details = pd.read_sql("SELECT * FROM [Order Details]", engine)
customers = pd.read_sql("SELECT * FROM Customers", engine)
products = pd.read_sql("SELECT * FROM Products", engine)
employees = pd.read_sql("SELECT * FROM Employees", engine)
shippers = pd.read_sql("SELECT * FROM Shippers", engine)
categories = pd.read_sql("SELECT * FROM Categories", engine)

print("📥 Extraction tables brute : OK")

# Renommages sécurisés
order_details = order_details.rename(columns={
    "UnitPrice":"UnitPrice_detail",
    "Quantity":"Quantity_detail",
    "Discount":"Discount_detail"
})

products = products.rename(columns={
    "UnitPrice":"UnitPrice_product"
})

# ===================== DIMENSIONS =====================

dim_customer = customers[['CustomerID','CompanyName','ContactName','Country','City','Region']].copy()
dim_customer['customer_key'] = dim_customer.index + 1

dim_product = products[['ProductID','ProductName','SupplierID','CategoryID','UnitPrice_product']].copy()
dim_product['product_key'] = dim_product.index + 1

dim_employee = employees[['EmployeeID','LastName','FirstName','Title']].copy()
dim_employee['employee_key'] = dim_employee.index + 1

dim_shipper = shippers[['ShipperID','CompanyName','Phone']]
dim_shipper['shipper_key'] = dim_shipper.index + 1

dim_category = categories[['CategoryID','CategoryName']].copy()
dim_category['category_key'] = dim_category.index + 1

orders['OrderDate'] = pd.to_datetime(orders['OrderDate'])
dim_time = pd.DataFrame({'date': orders['OrderDate'].dropna().unique()})
dim_time['date'] = pd.to_datetime(dim_time['date'])
dim_time['year'] = dim_time['date'].dt.year
dim_time['month'] = dim_time['date'].dt.month
dim_time['day'] = dim_time['date'].dt.day
dim_time['time_key'] = dim_time.index + 1

print("📊 Dimensions OK")

# ===================== FACT TABLE =====================

fact_order = order_details.merge(orders, on="OrderID", how="left")
fact_order = fact_order.merge(dim_customer, on="CustomerID", how="left")
fact_order = fact_order.merge(dim_product, on="ProductID", how="left")
fact_order = fact_order.merge(dim_employee, on="EmployeeID", how="left")
fact_order = fact_order.merge(dim_shipper, left_on="ShipVia", right_on="ShipperID", how="left")
fact_order = fact_order.merge(dim_time[['date','time_key']], left_on='OrderDate', right_on='date', how="left")

# Calcul total ligne sécurisé
fact_order['line_total'] = fact_order['UnitPrice_detail'] * fact_order['Quantity_detail'] * (1 - fact_order['Discount_detail'])

fact_order = fact_order[['time_key','customer_key','product_key','employee_key','shipper_key',
                         'Quantity_detail','UnitPrice_detail','Discount_detail','line_total']]

print("🧮 FACT TABLE OK")

# ===================== EXPORT CSV =====================

dim_customer.to_csv("dim_customer.csv", index=False)
dim_product.to_csv("dim_product.csv", index=False)
dim_employee.to_csv("dim_employee.csv", index=False)
dim_shipper.to_csv("dim_shipper.csv", index=False)
dim_category.to_csv("dim_category.csv", index=False)
dim_time.to_csv("dim_time.csv", index=False)
fact_order.to_csv("fact_order.csv", index=False)

print("\n💾 Export CSV OK — TRANSFORMATION TERMINÉE AVEC SUCCÈS 🚀\n")
