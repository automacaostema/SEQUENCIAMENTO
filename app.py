import streamlit as st
import pandas as pd
from supabase import create_client

# Configuração simples
st.set_page_config(layout="wide")
st.title("🚀 PCP Stema - Versão Estável")

# Conexão - Teste de ping no banco
try:
    sec = st.secrets
    client = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])
    st.success("Conectado ao Supabase com sucesso!")
except Exception as e:
    st.error(f"Erro na conexão: {e}")

# Botão para listar dados das tabelas
if st.button("Carregar Dados"):
    try:
        t_data = client.table("tabela_tempos").select("*").execute().data
        d_data = client.table("tabela_desenhos").select("*").execute().data
        
        st.write("### Tabela Tempos")
        st.dataframe(pd.DataFrame(t_data))
        
        st.write("### Tabela Desenhos")
        st.dataframe(pd.DataFrame(d_data))
    except Exception as e:
        st.error(f"Erro ao buscar tabelas: {e}")
