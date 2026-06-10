import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Sistema Stema - Debug", layout="wide")
st.title("🚀 Sistema de Sequenciamento - Modo Segurança")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=300)
def carregar_dados():
    tempos = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    desenhos = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
    return tempos, desenhos

df_tempos, df_desenhos = carregar_dados()

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    try:
        df_pcp = pd.read_excel(uploaded_file)
        # Mostra as colunas que ele está vendo para garantirmos que os nomes batem
        st.write("Colunas detectadas:", df_pcp.columns.tolist())
        
        # Limpeza básica (sem forçar tipos que quebram)
        df_pcp.columns = df_pcp.columns.str.strip()
        
        # Exibe a tabela bruta primeiro para ver se subiu
        st.dataframe(df_pcp)
        
        st.success("Planilha lida com sucesso!")
        
    except Exception as e:
        st.error(f"Erro na leitura: {e}")
