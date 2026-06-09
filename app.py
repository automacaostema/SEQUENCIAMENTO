import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Gestão de Produção", layout="wide")

st.title("Sequenciamento de Produção - Stema Usinagem")

# Conexão básica (o Supabase vai ler das secrets do Streamlit/Vercel)
# st.secrets['SUPABASE_URL'] e st.secrets['SUPABASE_KEY']

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("Dados da planilha carregados:")
    st.dataframe(df)
    st.success("Planilha processada com sucesso!")
