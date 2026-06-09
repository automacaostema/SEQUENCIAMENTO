import streamlit as st
import pandas as pd
from supabase import create_client

# 1. Configuração Inicial
st.set_page_config(page_title="Sistema Stema", layout="wide")
st.title("🚀 Sistema de Sequenciamento - Stema")

# 2. Conexão com Supabase
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# 3. Carregamento dos Bancos
@st.cache_data
def carregar_dados():
    # Buscamos os dados
    tempos = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    desenhos = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
    return tempos, desenhos

df_tempos, df_desenhos = carregar_dados()

# DEBUG: Vamos imprimir as colunas que o banco trouxe
st.write("Colunas encontradas no banco 'tabela_desenhos':", df_desenhos.columns.tolist())

# 4. Interface de Upload
uploaded_file = st.file_uploader("Upload da Planilha PCP (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    # Pegamos o nome correto da coluna do banco automaticamente
    coluna_banco = df_desenhos.columns[0] # Assume que a 1ª coluna é o código do desenho
    
    def calcular_sequenciamento(row):
        desenho_alvo = str(row['numero_desenho']).strip()
        
        # Filtra usando a coluna_banco que o sistema detectou
        filtro = df_desenhos[df_desenhos[coluna_banco].astype(str).str.strip() == desenho_alvo]
        
        if not filtro.empty:
            ferramentas_str = str(filtro['ferramentas_necessarias'].values[0])
            ferramentas = [f.strip() for f in ferramentas_str.split(',')]
            tempo_setup = df_tempos[df_tempos['nome_ferramenta'].isin(ferramentas)]['tempo_montagem'].sum()
            return tempo_setup + (row['tempo_unitario'] * row['quantidade'])
        return 0

    df_pcp['tempo_total_os'] = df_pcp.apply(calcular_sequenciamento, axis=1)
    st.dataframe(df_pcp)
