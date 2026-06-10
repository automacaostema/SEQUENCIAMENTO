import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Sistema Stema - PCP", layout="wide")
st.title("🚀 Sequenciamento e Otimização - Stema")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=300)
def carregar_dados():
    tempos = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    desenhos = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
    return tempos, desenhos

df_tempos, df_desenhos = carregar_dados()

def limpar_tempo(val):
    try:
        if isinstance(val, str) and ':' in val:
            partes = val.split(':')
            return float(partes[0]) * 60 + float(partes[1])
        return float(val)
    except:
        return 0.0

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    # Padroniza nomes de colunas para minúsculo para evitar erro
    df_pcp.columns = df_pcp.columns.str.lower().str.strip()
    
    # Processamento dos dados
    df_pcp['codigo interno'] = df_pcp['codigo interno'].astype(str).str.strip()
    df_pcp['tempo unidade'] = df_pcp['tempo unidade'].apply(limpar_tempo)
    df_pcp['quantidade'] = pd.to_numeric(df_pcp['quantidade'], errors='coerce').fillna(0)

    def calcular_linha(row):
        cod = row['codigo interno']
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == cod]
        if not filtro.empty:
            ferramentas = str(filtro['ferramentas_necessarias'].values[0]).split(',')
            tempo_setup = 0
            for f in ferramentas:
                tempo_setup += df_tempos[df_tempos['nome_ferramenta'].str.lower() == f.strip().lower()]['tempo_montagem'].sum()
            return float(tempo_setup) + (float(row['tempo unidade']) * float(row['quantidade']))
        return 0.0

    # Adiciona as colunas necessárias
    df_pcp['tempo_total_os'] = df_pcp.apply(calcular_linha, axis=1)
    
    # Busca grupo de ferramentas para sequenciamento
    def pegar_grupo(row):
        cod = row['codigo interno']
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == cod]
        return str(filtro['ferramentas_necessarias'].values[0]) if not filtro.empty else "sem_ferramenta"
    
    df_pcp['ferramental_grupo'] = df_pcp.apply(pegar_grupo, axis=1)
    
    # Ordenação profissional
    df_sequenciado = df_pcp.sort_values(by=['ferramental_grupo', 'data de entrega', 'tempo_total_os'])
    
    st.success("Sequenciamento organizado!")
    st.dataframe(df_sequenciado)
