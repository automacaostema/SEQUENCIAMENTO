import datetime as dt
import pandas as pd
import streamlit as st
from supabase import create_client

# --- Configurações Iniciais ---
st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# Conexão com Supabase
@st.cache_resource
def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

client = get_client()

# Carregamento de dados
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        t_data = client.table("tabela_tempos").select("*").execute().data
        d_data = client.table("tabela_desenhos").select("*").execute().data
        return pd.DataFrame(t_data), pd.DataFrame(d_data)
    except:
        return pd.DataFrame(), pd.DataFrame()

# Menu lateral
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# --- Lógica de Navegação ---
if menu == "🚀 Sequenciamento":
    st.write("### 🚀 Sequenciamento PCP")
    up = st.file_uploader("Planilha", type=["xlsx", "csv"])
    if up:
        st.success("Planilha carregada com sucesso!")
        # (Aqui você pode colar o restante da sua lógica de processamento depois)

elif menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    df_tempos, _ = carregar_dados()
    df_editado = st.data_editor(df_tempos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Tempos"):
        dados = df_editado.to_dict(orient="records")
        client.table("tabela_tempos").upsert(dados, on_conflict="nome_ferramenta").execute()
        st.cache_data.clear()
        st.rerun()

elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    _, df_desenhos = carregar_dados()
    df_editado = st.data_editor(df_desenhos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Desenhos"):
        dados = df_editado.to_dict(orient="records")
        client.table("tabela_desenhos").upsert(dados, on_conflict="numero_desenho").execute()
        st.cache_data.clear()
        st.rerun()
