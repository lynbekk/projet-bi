import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
from io import BytesIO
import os


# ===================== PAGE CONFIG =====================
st.set_page_config(page_title="Northwind BI", layout="wide")

# ===================== STYLE (dark mode) =====================
st.markdown("""
<style>
    body { background-color:#0b0f12; color:#ddd; }
    .title { font-size:32px; font-weight:800; color:#00E0FF; margin-bottom: -5px; }
    .subtitle { color:#999; margin-top:0px; }
    .card {
        background:#0f1720;
        padding:14px;
        border-radius:10px;
        text-align:center;
        color:white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    }
    .metric { font-size:24px; font-weight:700; color:#00FF9D; }
</style>
""", unsafe_allow_html=True)

# ===================== LOAD DATA (SQL OR UNIFIED) =====================
import os


    # ===================== LOAD DATA =====================

unified = "data/fact_order_unified.csv"
sql_fact = "data/fact_order.csv"

# Charger la table fact unifiée si elle existe
if os.path.exists(unified):
    fact = pd.read_csv(unified)
    
else:
    fact = pd.read_csv(sql_fact)
    

# Les autres dimensions ne changent pas
product   = pd.read_csv("data/dim_product.csv")
category  = pd.read_csv("data/dim_category.csv")
time      = pd.read_csv("data/dim_time.csv")

# Harmonisation des colonnes Access → SQL si nécessaire
fact = fact.rename(columns={
    "Quantity": "quantity",
    "Unit Price": "unit_price",
    "Discount": "discount",
})

# Assurer line_total cohérent
if "line_total" not in fact.columns:
    if {"quantity", "unit_price"}.issubset(fact.columns):
        fact["line_total"] = fact["quantity"] * fact["unit_price"] * (1 - fact.get("discount", 0))
    else:
        st.error("❌ Impossible de calculer line_total : colonnes manquantes.")
else:
    
    fact = pd.read_csv("data/fact_order.csv")

product  = pd.read_csv("data/dim_product.csv")
category = pd.read_csv("data/dim_category.csv")
time     = pd.read_csv("data/dim_time.csv")

# ===================== MERGE =====================
df = (
    fact.merge(product, on="product_key", how="left")
        .merge(category, on="CategoryID", how="left")
        .merge(time, on="time_key", how="left")
)

# ===================== CORRECTIONS DES DONNÉES SQL + ACCESS =====================
df["line_total"] = df["line_total"].astype(float)
df["month"] = df["month"].astype(str)
df["year"]  = df["year"].astype(str)

# Fix Access values such as "1996.0"
df["year"]  = df["year"].str.replace(".0", "", regex=False)
df["month"] = df["month"].str.replace(".0", "", regex=False)

# Convert to int
df["year_int"] = df["year"].astype(int)
df["month_int"] = df["month"].astype(int)

# Proper datetime
df["year_month"] = pd.to_datetime(
    df["year_int"].astype(str) + "-" + df["month_int"].astype(str).str.zfill(2) + "-01"
)

# ===================== HEADER =====================
st.markdown("<div class='title'> Business Intelligence – Northwind</div>", unsafe_allow_html=True)


st.write("")

# ===================== SIDEBAR FILTERS =====================
st.sidebar.header("Filtres")

years = sorted(df["year"].unique())
sel_year = st.sidebar.selectbox("Année", years, index=len(years)-1)

sel_category = st.sidebar.multiselect(
    "Catégorie (facultatif)",
    options=sorted(df["CategoryName"].dropna().unique()),
)

sel_product = st.sidebar.multiselect(
    "Produit (facultatif)",
    options=sorted(df["ProductName"].dropna().unique()),
)

# Apply filters
df_filtered = df[df["year"] == sel_year]

if sel_category:
    df_filtered = df_filtered[df_filtered["CategoryName"].isin(sel_category)]

if sel_product:
    df_filtered = df_filtered[df_filtered["ProductName"].isin(sel_product)]

# ===================== KPIs =====================
st.subheader("⭐ Indicateurs Clés")
col1, col2, col3, col4 = st.columns(4)

total_revenue = df_filtered["line_total"].sum()
avg_order = df_filtered["line_total"].mean() if len(df_filtered) > 0 else 0
unique_customers = df_filtered["customer_key"].nunique()
top_product = (
    df_filtered.groupby("ProductName")["line_total"].sum().idxmax()
    if not df_filtered.empty else "Aucun"
)

col1.metric("💰 CA (filtré)", f"{total_revenue:,.2f} $")
col2.metric("🧾 Panier moyen", f"{avg_order:,.2f} $")
col3.metric("👥 Clients uniques", f"{unique_customers}")
col4.metric("🏆 Top produit", top_product)

# ===================== VISUALISATIONS =====================
st.subheader("📈 Visualisations")

agg_all = df.groupby("year_month")["line_total"].sum().reset_index()
agg_filtered = df_filtered.groupby("year_month")["line_total"].sum().reset_index()

# Ligne CA filtré
st.markdown("**Historique (filtré)** — CA par mois")
fig_hist = px.line(
    agg_filtered, x="year_month", y="line_total",
    markers=True, title="CA mensuel (filtré)"
)
st.plotly_chart(fig_hist, use_container_width=True)

# Top produits
st.markdown("**Top Produits (filtré)**")
top10 = (
    df_filtered.groupby("ProductName")["line_total"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
fig_top = px.bar(top10, x="ProductName", y="line_total", text_auto=True)
st.plotly_chart(fig_top, use_container_width=True)

# Catégories
st.markdown("**Répartition par catégorie (filtré)**")
cat_sales = df_filtered.groupby("CategoryName")["line_total"].sum().reset_index()
if not cat_sales.empty:
    fig_pie = px.pie(cat_sales, names="CategoryName", values="line_total")
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("Aucune donnée.")

# ===================== PREVISION =====================
st.subheader("🔮 Prévision des ventes")

horizon = st.slider("Horizon (mois)", 1, 24, 12)
method = st.selectbox("Méthode", ["Régression linéaire", "Croissance moyenne (%)"])
base = st.radio("Base historique", ["Toutes années", "Données filtrées"])

series = agg_all if base == "Toutes années" else agg_filtered

if series.empty:
    st.warning("Pas assez de données.")
else:
    series = series.set_index("year_month").asfreq("MS").fillna(0).reset_index()
    y = series["line_total"].values
    x = np.arange(len(y))

    if method == "Régression linéaire":
        a, b = np.polyfit(x, y, 1)
        future_x = np.arange(len(y), len(y)+horizon)
        forecast_vals = np.maximum(a*future_x + b, 0)
    else:
        pct = pd.Series(y).pct_change().replace([np.inf, -np.inf], 0).fillna(0)
        g = pct.mean()
        last = y[-1]
        forecast_vals = [max(0, last := last * (1+g)) for _ in range(horizon)]

    future_dates = pd.date_range(series["year_month"].max() + pd.offsets.MonthBegin(1),
                                 periods=horizon, freq="MS")

    df_forecast = pd.DataFrame({"year_month": future_dates, "forecast": forecast_vals})

    combined = pd.concat([
        series.rename(columns={"line_total":"value"}),
        df_forecast.rename(columns={"forecast":"value"})
    ])

    fig_forecast = px.line(combined, x="year_month", y="value", title="Prévision")
    st.plotly_chart(fig_forecast, use_container_width=True)

    st.dataframe(df_forecast)

    csv = df_forecast.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Télécharger prévision CSV", csv, "forecast.csv")

# ===================== PDF REPORT =====================
st.markdown("---")
st.subheader("📄 Rapport PDF")

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

if st.button(" Générer Rapport PDF"):
    file_name = f"rapport_northwind_{datetime.date.today()}.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 800, "RAPPORT NORTHWIND - SYNTHÈSE")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 770, "KPIs (filtrés):")
    c.setFont("Helvetica", 11)
    c.drawString(60, 750, f"CA total: {total_revenue:,.2f} $")
    c.drawString(60, 735, f"Panier moyen: {avg_order:,.2f} $")
    c.drawString(60, 720, f"Clients uniques: {unique_customers}")
    c.drawString(60, 705, f"Top produit: {top_product}")

    c.save()
    st.success(f"PDF généré : {file_name}")
    st.download_button("⬇ Télécharger le PDF", open(file_name, "rb"), file_name)

# ===================== FOOTER =====================
st.markdown("---")
st.write("© Projet BI — Northwind ")
