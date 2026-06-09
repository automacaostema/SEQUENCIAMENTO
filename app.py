import streamlit as st
from supabase import create_client

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("Teste de Conexão")

# Tenta ler a tabela
try:
    dados = supabase.table("tabela_desenhos").select("*").execute()
    st.write("Dados brutos do Supabase:", dados.data)
except Exception as e:
    st.error(f"Erro: {e}")
