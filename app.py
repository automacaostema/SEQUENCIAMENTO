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

def limpar_tempo(val):
    try:
        # Se for string com horas
        if isinstance(val, str) and ':' in val:
            partes = val.split(':')
            return float(partes[0]) * 60 + float(partes[1])
        # Tenta converter direto para número
        return float(val)
    except:
        return 0.0

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    # Normalização da busca
    df_pcp['codigo interno'] = df_pcp['codigo interno'].astype(str).str.strip()
    df_desenhos['numero_desenho'] = df_desenhos['numero_desenho'].astype(str).str.strip()

    # Conversão de valores
    df_pcp['tempo unidade'] = df_pcp['tempo unidade'].apply(limpar_tempo)
    df_pcp['quantidade'] = pd.to_numeric(df_pcp['quantidade'], errors='coerce').fillna(0)

    def calcular_linha(row):
        cod_pcp = row['codigo interno']
        # Busca exata no banco
        filtro = df_desenhos[df_desenhos['numero_desenho'] == cod_pcp]
        
        if not filtro.empty:
            ferramentas = str(filtro['ferramentas_necessarias'].values[0]).lower().split(',')
            tempo_setup = df_tempos[df_tempos['nome_ferramenta'].str.lower().isin(ferramentas)]['tempo_montagem'].sum()
            return float(tempo_setup) + (float(row['tempo unidade']) * float(row['quantidade']))
        return 0.0

    def buscar_ferramental(row):
        cod_pcp = row['codigo interno']
        filtro = df_desenhos[df_desenhos['numero_desenho'] == cod_pcp]
        return str(filtro['ferramentas_necessarias'].values[0]) if not filtro.empty else "sem_ferramenta"

    # Processamento
    df_pcp['tempo_total_os'] = df_pcp.apply(calcular_linha, axis=1)
    df_pcp['ferramental_grupo'] = df_pcp.apply(buscar_ferramental, axis=1)
    
    # Ordenação
    df_sequenciado = df_pcp.
