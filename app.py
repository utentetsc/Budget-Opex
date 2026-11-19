import streamlit as st
import pandas as pd
import json
import plotly.express as px

st.set_page_config(page_title="The Space Budget Allocator", layout="wide")

# Carica JSON
@st.cache_data
def load_data():
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

data = load_data()
df = pd.DataFrame(data["cinemas"])

st.title("🎬 The Space Cinema - Budget Allocator")
st.markdown(f"**{len(df)} cinema** caricati da `data.json`")

# SIDEBAR
st.sidebar.header("⚙️ Configurazione")
total_budget = st.sidebar.number_input("💰 Budget Totale (€)", value=1_000_000, step=10_000)
anno_rif = st.sidebar.number_input("📅 Anno di riferimento", value=2026)

st.sidebar.subheader("⚖️ Pesi del coefficiente")
w_eta = st.sidebar.slider("Peso Età", 0.0, 1.0, 0.5)
w_pres = st.sidebar.slider("Peso Presenze", 0.0, 1.0, 0.3)
w_sup = st.sidebar.slider("Peso Superficie", 0.0, 1.0, 0.2)

# Calcoli
df["eta"] = anno_rif - df["anno_costr"]
df["fattore_reno"] = df["anno_ristrutt"].apply(
    lambda x: 0.8 if (anno_rif - x) < 5 else 1.2 if pd.isna(x) or (anno_rif - x) > 15 else 1.0
)
df["fattore_tipo"] = df["tipo"].apply(lambda x: 1.3 if x == "Stand-alone" else 1.0)
df["fattore_tetto"] = df["tetto"].apply(lambda x: 1.5 if x == "Vecchio" else 1.0)
df["fattore_resp"] = df["resp_straord"].apply(lambda x: 0.7 if x == "Proprietà" else 1.0)

max_pres = df["presenze"].max()
max_sup = df["mq"].max()
df["score_pres"] = (df["presenze"] / max_pres) * 100
df["score_sup"] = (df["mq"] / max_sup) * 100

df["coeff_raw"] = (
    (df["eta"] * w_eta * 10) +
    (df["score_pres"] * w_pres) +
    (df["score_sup"] * w_sup)
) * df["fattore_reno"] * df["fattore_tipo"] * df["fattore_tetto"] * df["fattore_resp"]

tot_coeff = df["coeff_raw"].sum()
df["perc_budget"] = (df["coeff_raw"] / tot_coeff) * 100
df["budget_assegnato"] = total_budget * (df["perc_budget"] / 100)

# METRICS
col1, col2, col3, col4 = st.columns(4)
col1.metric("Cinema", len(df))
col2.metric("Budget Totale", f"€ {total_budget:,.0f}")
col3.metric("Tetto Vecchio", len(df[df["tetto"]=="Vecchio"]))
col4.metric("Stand-alone", len(df[df["tipo"]=="Stand-alone"]))

# TABS
tab1, tab2, tab3, tab4 = st.tabs(["🎬 Cinema", "📊 Grafici", "📋 Ordini Storici", "🗂️ Categorie"])

with tab1:
    st.subheader("Tabella completa")
    st.dataframe(
        df[["nome","area","fm","eta","tipo","tetto","anno_ristrutt","resp_straord",
            "coeff_raw","perc_budget","budget_assegnato"]]
        .sort_values("budget_assegnato", ascending=False)
        .style.format({
            "perc_budget": "{:.2f}%",
            "budget_assegnato": "€ {:,.0f}",
            "coeff_raw": "{:.2f}"
        }),
        use_container_width=True
    )

with tab2:
    st.subheader("Budget per Cinema")
    fig = px.bar(
        df.sort_values("budget_assegnato", ascending=True),
        x="budget_assegnato", y="nome", orientation="h",
        color="tipo", title="Budget assegnato"
    )
    st.plotly_chart(fig, use_container_width