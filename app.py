import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema - Modo Recuperação")

# Conexão
sec = st.secrets
client = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])

# Carregar dados
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        t = client.table("tabela_tempos").select("*").execute().data
        d = client.table("tabela_desenhos").select("*").execute().data
        return pd.DataFrame(t), pd.DataFrame(d)
    except Exception as e:
        st.error(f"Erro ao carregar banco: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_tempos, df_desenhos = carregar_dados()

# Abas simples
menu = st.sidebar.radio("Navegação", ["🔧 Tabela Tempos", "📐 Tabela Desenhos"])

if menu == "🔧 Tabela Tempos":
    df_ed = st.data_editor(df_tempos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar"):
        client.table("tabela_tempos").upsert(df_ed.to_dict(orient="records"), on_conflict="nome_ferramenta").execute()
        st.cache_data.clear()
        st.rerun()

elif menu == "📐 Tabela Desenhos":
    df_ed = st.data_editor(df_desenhos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar"):
        client.table("tabela_desenhos").upsert(df_ed.to_dict(orient="records"), on_conflict="numero_desenho").execute()
        st.cache_data.clear()
        st.rerun()
