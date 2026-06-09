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
        if hasattr(val, 'hour'):
            return float(val.hour * 60 + val.minute)
        if isinstance(val, str):
            if ':' in val:
                partes = val.split(':')
                return float(partes[0]) * 60 + float(partes[1])
            return float(val)
        return float(val)
    except:
        return 0.0

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    # Limpeza
    df_pcp['tempo unidade'] = df_pcp['tempo unidade'].apply(limpar_tempo)
    df_pcp['quantidade'] = pd.to_numeric(df_pcp['quantidade'], errors='coerce').fillna(0)
    
    def calcular_linha(row):
        cod = str(row['codigo interno']).strip()
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == cod]
        
        if not filtro.empty:
            ferramentas = str(filtro['ferramentas_necessarias'].values[0]).lower().split(',')
            tempo_setup = df_tempos[df_tempos['nome_ferramenta'].str.lower().isin(ferramentas)]['tempo_montagem'].sum()
            # Cálculo completo com parênteses corrigidos
            return float(tempo_setup) + (float(row['tempo unidade']) * float(row['quantidade']))
        return 0.0

    def buscar_ferramental(row):
        cod = str(row['codigo interno']).strip()
        fil
