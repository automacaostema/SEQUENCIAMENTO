import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Sistema Stema - PCP", layout="wide")
st.title("🚀 Sequenciamento e Otimização de Setup - Stema")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=60)
def carregar_dados():
    tempos = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    desenhos = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
    return tempos, desenhos

df_tempos, df_desenhos = carregar_dados()

uploaded_file = st.file_uploader("Suba a planilha atualizada do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    # Limpeza de colunas numéricas com os novos nomes
    df_pcp['tempo unidade'] = pd.to_numeric(df_pcp['tempo unidade'], errors='coerce').fillna(0)
    df_pcp['quantidade'] = pd.to_numeric(df_pcp['quantidade'], errors='coerce').fillna(0)
    df_pcp['data de entrega'] = pd.to_datetime(df_pcp['data de entrega'])
    
    def calcular_linha(row):
        cod = str(row['codigo interno']).strip()
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == cod]
        
        if not filtro.empty:
            ferramentas = str(filtro['ferramentas_necessarias'].values[0]).lower().split(',')
            tempo_setup = df_tempos[df_tempos['nome_ferramenta'].str.lower().isin(ferramentas)]['tempo_montagem'].sum()
            return float(tempo_setup) + (float(row['tempo unidade']) * float(row['quantidade']))
        return 0.0

    def buscar_ferramental(row):
        cod = str(row['codigo interno']).strip()
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == cod]
        return str(filtro['ferramentas_necessarias'].values[0]) if not filtro.empty else "sem_ferramenta"

    # Processamento
    df_pcp['tempo_total_os'] = df_pcp.apply(calcular_linha, axis=1)
    df_pcp['ferramental_grupo'] = df_pcp.apply(buscar_ferramental, axis=1)
    
    # Otimização: Setup primeiro, Data de entrega depois
    df_sequenciado = df_pcp.sort_values(
        by=['ferramental_grupo', 'data de entrega', 'tempo_total_os'], 
        ascending=[True, True, True]
    )
    
    st.success("Sequenciamento otimizado com a nova estrutura!")
    # Exibe a tabela, incluindo a coluna 'n servico' que você pediu
    st.dataframe(df_sequenciado)
