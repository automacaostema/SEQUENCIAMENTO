import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

# Layout minimalista com tema escuro
st.set_page_config(layout="wide", page_title="PCP Stema")
st.markdown("""
    <style>
    .stMetric { background-color: #0E1117; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    h1 { color: #FAFAFA; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 PCP Stema")

sec = st.secrets
client = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])

# --- FUNÇÕES DE FORMATO ---
def formatar_numero(n):
    # Formata: 3.685 em vez de 3,685
    return f"{int(n):,.0f}".replace(",", ".")

# --- LÓGICA DO PCP ---
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

if menu == "🚀 Sequenciamento":
    if "df_seq" in st.session_state:
        df_temp = st.session_state["df_seq"]
        
        # Visores estilizados
        c1, c2 = st.columns(2)
        c1.metric("📦 Peças a Produzir", formatar_numero(df_temp['quantidade'].sum()))
        c2.metric("⏱️ Horas Totais", f"{df_temp['Total (Horas)'].sum():.2f}".replace(".", ",").replace(",", "."))
        st.markdown("---")

    up = st.file_uploader("📂 Upload Planilha de Produção", type=["xlsx", "csv"])
    
    # ... (Restante da sua lógica de processamento se mantém igual) ...
