import streamlit as st
import pandas as pd
from supabase import create_client

# Configuração da conexão
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# Função para buscar dados
def get_data(table):
    response = supabase.table(table).select("*").execute()
    # Converte a resposta em DataFrame
    df = pd.DataFrame(response.data)
    return df

# Carregar os dados
df_tempos = get_data("tabela_tempos") 

st.write("Banco de Ferramentas Carregado:")
st.dataframe(df_tempos)
