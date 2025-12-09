import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///northwind_dwh.db")  # DWH local simple et rapide

for tbl in ["dim_customer","dim_product","dim_employee","dim_shipper","dim_category","dim_time","fact_order"]:
    df = pd.read_csv(f"{tbl}.csv")
    df.to_sql(tbl, engine, if_exists='replace', index=False)
    print(f"✔ {tbl} chargé dans le DWH")

print("\n🍾 DATA WAREHOUSE PRÊT !")
