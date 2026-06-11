import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# Conexão
sec = st.secrets
client = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        t = client.table("tabela_tempos").select("*").execute().data
        d = client.table("tabela_desenhos").select("*").execute().data
        return pd.DataFrame(t), pd.DataFrame(d)
    except: return pd.DataFrame(), pd.DataFrame()

df_tempos, df_desenhos = carregar_dados()

def limpar_tempo(val):
    try:
        if isinstance(val, (int, float)): return float(val)
        if isinstance(val, str):
            p = [float(x) for x in val.split(":")]
            return p[0]*60 + p[1] + (p[2]/60.0) if len(p)==3 else (p[0] + p[1]/60.0 if len(p)==2 else float(p[0]))
        return 0.0
    except: return 0.0

menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

if menu == "🚀 Sequenciamento":
    up = st.file_uploader("Planilha", type=["xlsx", "csv"])
    if up:
        df_raw = pd.read_excel(up)
        df_raw.columns = [c.strip() for c in df_raw.columns]
        df_raw["tempo unitário (min)"] = df_raw["tempo unidade"].apply(limpar_tempo)
        df_editado = st.data_editor(df_raw, use_container_width=True)
        st.write("Dados processados com sucesso.")

elif menu == "🔧 Tabela Tempos":
    df_ed = st.data_editor(df_tempos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar"):
        client.table("tabela_tempos").upsert(df_ed.to_dict("records"), on_conflict="nome_ferramenta").execute()
        st.cache_data.clear(); st.rerun()

elif menu == "📐 Tabela Desenhos":
    df_ed = st.data_editor(df_desenhos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar"):
        client.table("tabela_desenhos").upsert(df_ed.to_dict("records"), on_conflict="numero_desenho").execute()
        st.cache_data.clear(); st.rerun()
