import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
from io import BytesIO

# ===================== PAGE CONFIG =====================
st.set_page_config(page_title="Northwind BI ", layout="wide")

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

# ===================== LOAD DATA =====================
fact  = pd.read_csv("data/fact_order.csv")
product = pd.read_csv("data/dim_product.csv")
category = pd.read_csv("data/dim_category.csv")
time  = pd.read_csv("data/dim_time.csv")

# ===================== MERGE =====================
# product has CategoryID, dim_category has CategoryID
df = fact.merge(product, on="product_key", how="left") \
         .merge(category, on="CategoryID", how="left") \
         .merge(time, on="time_key", how="left")

# ensure types and canonical columns
df["line_total"] = df["line_total"].astype(float)
df["month"] = df["month"].astype(str)
df["year"]  = df["year"].astype(str)

# Build a proper datetime index for monthly aggregation
# time table has 'year' and 'month' columns (as strings)
df["year_int"] = df["year"].astype(int)
df["month_int"] = df["month"].astype(int)
df["year_month"] = pd.to_datetime(df["year_int"].astype(str) + "-" + df["month_int"].astype(str).str.zfill(2) + "-01")

# ===================== HEADER =====================
st.markdown("<div class='title'> Business Intelligence – Northwind</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Dashboard complet — KPIs, visualisations, filtres et prévision.</div>", unsafe_allow_html=True)
st.write("")

# ===================== SIDEBAR FILTERS =====================
st.sidebar.header("Filtres")
years = sorted(df["year"].unique())
sel_year = st.sidebar.selectbox("Année", years, index=len(years)-1)
sel_category = st.sidebar.multiselect("Catégorie (facultatif)", options=df["CategoryName"].sort_values().unique(), default=None)
sel_product = st.sidebar.multiselect("Produit (facultatif)", options=df["ProductName"].sort_values().unique(), default=None)

# apply filters
df_filtered = df[df["year"] == sel_year]
if sel_category and len(sel_category) > 0:
    df_filtered = df_filtered[df_filtered["CategoryName"].isin(sel_category)]
if sel_product and len(sel_product) > 0:
    df_filtered = df_filtered[df_filtered["ProductName"].isin(sel_product)]

# ===================== KPIs =====================
st.subheader("⭐ Indicateurs Clés")
col1, col2, col3, col4 = st.columns(4)

total_revenue = df_filtered["line_total"].sum()
avg_order = df_filtered["line_total"].mean() if len(df_filtered)>0 else 0
unique_customers = df_filtered["customer_key"].nunique()
top_product = df_filtered.groupby("ProductName")["line_total"].sum().idxmax() if not df_filtered.empty else "N/A"

col1.metric("💰 CA (filtré)", f"{total_revenue:,.2f} $")
col2.metric("🧾 Panier moyen", f"{avg_order:,.2f} $")
col3.metric("👥 Clients uniques", f"{unique_customers}")
col4.metric("🏆 Top produit", f"{top_product}")

st.write("")

# ===================== VISUALISATIONS =====================
st.subheader("📈 Visualisations")

# monthly series (historical) aggregated from full df (not only filtered timeframe) for forecasting baseline,
# but show filtered monthly series for display if user wants.
agg_all = df.groupby("year_month")["line_total"].sum().reset_index().sort_values("year_month")
agg_filtered = df_filtered.groupby("year_month")["line_total"].sum().reset_index().sort_values("year_month")

# plot historical for filtered data
st.markdown("**Historique (filtré)** — CA par mois")
fig_hist = px.line(agg_filtered, x="year_month", y="line_total", markers=True, title="CA mensuel (filtré)")
fig_hist.update_layout(xaxis_title="Date", yaxis_title="CA")
st.plotly_chart(fig_hist, use_container_width=True)

# top products
st.markdown("**Top Produits (filtré)**")
top10 = df_filtered.groupby("ProductName")["line_total"].sum().sort_values(ascending=False).head(10).reset_index()
fig_top = px.bar(top10, x="ProductName", y="line_total", title="Top 10 produits", text_auto=True)
st.plotly_chart(fig_top, use_container_width=True)

# categories pie
st.markdown("**Répartition par catégorie (filtré)**")
cat_sales = df_filtered.groupby("CategoryName")["line_total"].sum().reset_index()
if not cat_sales.empty:
    fig_pie = px.pie(cat_sales, names="CategoryName", values="line_total", title="Part CA par catégorie")
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("Aucune donnée pour cette sélection.")

# ===================== FORECAST (simple, robuste) =====================
st.subheader("🔮 Prévision : régression linéaire sur la série temporelle mensuelle")

# Forecast settings
horizon = st.slider("Horizon (mois)", min_value=1, max_value=24, value=12)
method = st.selectbox("Méthode simple", ["Régression linéaire (trend)", "Croissance moyenne (%)"], index=0)

# choose baseline series for forecasting: use agg_all (full history) or agg_filtered (user choice)
use_history = st.radio("Base historique pour la prévision", ("Toutes années", "Données filtrées"), index=0)
series = agg_all if use_history == "Toutes années" else agg_filtered

if series.empty or series["line_total"].sum() == 0:
    st.warning("Pas assez de données pour faire une prévision.")
else:
    # ensure continuous monthly index
    series = series.set_index("year_month").asfreq("MS").fillna(0).reset_index()
    series = series.sort_values("year_month")
    y = series["line_total"].values
    x = np.arange(len(y))

    if method == "Régression linéaire (trend)":
        # linear fit y = a*x + b
        coef = np.polyfit(x, y, 1)
        a, b = coef[0], coef[1]
        future_x = np.arange(len(y), len(y) + horizon)
        forecast_vals = a * future_x + b
        # avoid negatives
        forecast_vals = np.where(forecast_vals < 0, 0, forecast_vals)
    else:
        # average monthly growth rate (pct change), apply multiplicative growth
        pct_changes = pd.Series(y).pct_change().replace([np.inf, -np.inf], 0).fillna(0)
        avg_growth = pct_changes.mean()
        last = y[-1]
        forecast_vals = []
        current = last
        for i in range(horizon):
            current = current * (1 + avg_growth)
            forecast_vals.append(max(0, current))
        forecast_vals = np.array(forecast_vals)

    # build forecast dataframe
    last_date = series["year_month"].max()
    # generate future month dates
    future_dates = pd.date_range(start=last_date + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    df_forecast = pd.DataFrame({"year_month": future_dates, "forecast": forecast_vals})

    # plot combined
    combined = pd.concat([
        series[["year_month", "line_total"]].rename(columns={"line_total": "value"}),
        pd.DataFrame({"year_month": df_forecast["year_month"], "value": df_forecast["forecast"]})
    ], ignore_index=True)
    combined = combined.sort_values("year_month")

    fig_forecast = px.line(combined, x="year_month", y="value", title=f"Historique + Prévision ({horizon} mois)", markers=True)
    fig_forecast.add_vrect(x0=series["year_month"].min(), x1=series["year_month"].max(), fillcolor="LightBlue", opacity=0.1, layer="below", line_width=0)
    st.plotly_chart(fig_forecast, use_container_width=True)

    # show forecast table and allow download
    st.subheader("📥 Prévision – Tableau")
    st.dataframe(df_forecast.rename(columns={"year_month":"Mois", "forecast":"Prévision_CA"}))

    # allow CSV download
    csv_buf = df_forecast.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Télécharger prévision CSV", data=csv_buf, file_name="forecast.csv", mime="text/csv")

# ===================== REPORT PDF BUTTON (SIMPLE SUMMARY) =====================
st.markdown("---")
st.subheader("📄 Générer un rapport PDF")

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

if st.button(" Générer Rapport PDF"):
    file_name = f"rapport_northwind_{datetime.date.today()}.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)

    # header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 800, "RAPPORT NORTHWIND - SYNTHÈSE")

    # KPIs
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 770, "KPIs (filtrés):")
    c.setFont("Helvetica", 11)
    c.drawString(60, 750, f"CA total: {total_revenue:,.2f} $")
    c.drawString(60, 735, f"Panier moyen: {avg_order:,.2f} $")
    c.drawString(60, 720, f"Clients uniques: {unique_customers}")
    c.drawString(60, 705, f"Top produit: {top_product}")

    # short conclusion
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 675, "Conclusion & recommandations:")
    c.setFont("Helvetica", 11)
    c.drawString(60, 655, "- Vérifier le stock du top produit.")
    c.drawString(60, 640, "- Investir sur catégories en croissance.")
    c.drawString(60, 625, "- Poursuivre l'analyse clients géographiques.")

    c.save()
    st.success(f" Rapport généré : {file_name}")
    st.download_button("⬇ Télécharger le PDF", data=open(file_name, "rb"), file_name=file_name)

# ===================== FOOTER =====================
st.markdown("---")
st.write("© Projet BI — Northwind")

