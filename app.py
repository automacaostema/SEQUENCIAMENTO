import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

def invalidar_cache():
    st.cache_data.clear()

sec = st.secrets
url = sec["SUPABASE_URL"]
key = sec["SUPABASE_KEY"]
client = create_client(url, key)

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        t_tbl = client.table("tabela_tempos")
        d_tbl = client.table("tabela_desenhos")
        t_data = t_tbl.select("*").execute().data
        d_data = d_tbl.select("*").execute().data
        return pd.DataFrame(t_data), pd.DataFrame(d_data)
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_tempos, df_desenhos = carregar_dados()

# Sidebar
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# ESTRUTURA CORRETA: O primeiro deve ser sempre um 'if'
if menu == "🚀 Sequenciamento":
    st.write("Funcionalidade de sequenciamento ativa.")

elif menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    df_t_ed = st.data_editor(df_tempos, use_container_width=True, num_rows="dynamic")
    if st.button("💾 Atualizar Banco (Tempos)"):
        dict_t = df_t_ed.to_dict(orient="records")
        client.table("tabela_tempos").upsert(dict_t).execute()
        invalidar_cache()
        st.success("Banco de Tempos Atualizado!")
        st.rerun()

elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    df_d_ed = st.data_editor(df_desenhos, use_container_width=True, num_rows="dynamic")
    if st.button("💾 Atualizar Banco (Desenhos)"):
        dict_d = df_d_ed.to_dict(orient="records")
        client.table("tabela_desenhos").upsert(dict_d).execute()
        invalidar_cache()
        st.success("Banco de Desenhos Atualizado!")
        st.rerun()
