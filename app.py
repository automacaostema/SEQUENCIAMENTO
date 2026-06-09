import streamlit as st
import pandas as pd
from supabase import create_client

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("Sequenciamento Stema")

# Carrega bancos
try:
    df_tempos = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    df_desenhos = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
except Exception as e:
    st.error(f"Erro ao carregar tabelas: {e}")
    st.stop()

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    # Verifica nomes das colunas para evitar o erro de KeyError
    colunas_desenhos = df_desenhos.columns.tolist()
    
    def calcular_total(row):
        # Usa 'numero_Desenho' conforme sua confirmação no Supabase
        # E 'desenho' da sua planilha (ajuste para 'Desenho' se necessário)
        filtro = df_desenhos[df_desenhos['numero_desenho'] == row['desenho']]
        
        if not filtro.empty:
            ferramentas_str = filtro['ferramentas_necessarias'].values[0]
            ferramentas = [f.strip() for f in str(ferramentas_str).split(',')]
            
            # Soma os tempos
            tempo_setup = df_tempos[df_tempos['nome_ferramenta'].isin(ferramentas)]['tempo_montagem'].sum()
            
            return tempo_setup + (row['tempo_unitario'] * row['quantidade'])
        return 0

    try:
        df_pcp['tempo_total_os'] = df_pcp.apply(calcular_total, axis=1)
        st.success("Sequenciamento Gerado com sucesso!")
        st.dataframe(df_pcp)
    except KeyError as e:
        st.error(f"Erro de coluna na planilha ou banco: {e}")
        st.write("Colunas disponíveis no banco de desenhos:", colunas_desenhos)
        st.write("Colunas na sua planilha:", df_pcp.columns.tolist())
