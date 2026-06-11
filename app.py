import streamlit as st
import pandas as pd
from supabase import create_client
import datetime as dt

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# --- Configuração Supabase ---
@st.cache_resource
def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

client = get_client()

# --- Funções de Dados ---
@st.cache_data(ttl=60)
def carregar_dados():
    t_data = client.table("tabela_tempos").select("*").execute().data
    d_data = client.table("tabela_desenhos").select("*").execute().data
    return pd.DataFrame(t_data), pd.DataFrame(d_data)

# --- Sidebar ---
menu = st.sidebar.radio("Navegação", ["🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# --- Lógica de Salvamento (Corrigida) ---
if menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    df_t, _ = carregar_dados()
    df_editado = st.data_editor(df_t, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 Salvar Tempos"):
        # O on_conflict é vital para o Upsert funcionar sem duplicar
        dados = df_editado.to_dict(orient="records")
        try:
            client.table("tabela_tempos").upsert(dados, on_conflict="nome_ferramenta").execute()
            st.success("Dados salvos com sucesso!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    _, df_d = carregar_dados()
    df_editado = st.data_editor(df_d, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 Salvar Desenhos"):
        dados = df_editado.to_dict(orient="records")
        try:
            client.table("tabela_desenhos").upsert(dados, on_conflict="numero_desenho").execute()
            st.success("Dados salvos com sucesso!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
