import streamlit as st
import pandas as pd
from supabase import create_client

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("Sequenciamento Stema")

# Carrega bancos
df_tempos = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
df_desenhos = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    def calcular_total(row):
        # Busca ferramentas do desenho
        lista = df_desenhos.loc[df_desenhos['numero_desenho'] == row['desenho'], 'ferramentas_necessarias'].values
        if len(lista) > 0:
            ferramentas = lista[0].split(',')
            # Soma tempos
            tempo_setup = df_tempos[df_tempos['nome_ferramenta'].isin(ferramentas)]['tempo_montagem'].sum()
            return tempo_setup + (row['tempo_unitario'] * row['quantidade'])
        return 0

    df_pcp['tempo_total_os'] = df_pcp.apply(calcular_total, axis=1)
    st.write("Sequenciamento Gerado:", df_pcp)
