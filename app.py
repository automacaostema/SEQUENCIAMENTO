import streamlit as st
import pandas as pd
from supabase import create_client

# 1. Configuração
st.set_page_config(page_title="Sistema Stema", layout="wide")
st.title("🚀 Sistema de Sequenciamento - Stema")

# 2. Conexão
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# 3. Carregar dados
@st.cache_data(ttl=60)
def carregar_bancos():
    df_t = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    df_d = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
    return df_t, df_d

df_tempos, df_desenhos = carregar_bancos()

# 4. Função de limpeza de tempo
def converter_tempo(val):
    try:
        if isinstance(val, (pd.Timestamp, pd.Timedelta)):
            return val.hour * 60 + val.minute + val.second / 60
        return float(val)
    except:
        return 0.0

# 5. Interface
uploaded_file = st.file_uploader("Suba a planilha do PCP (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    # Limpa a coluna de tempo antes de calcular
    df_pcp['tempo_unitario'] = df_pcp['tempo_unitario'].apply(converter_tempo)
    
    def calcular_sequenciamento(row):
        desenho_alvo = str(row['numero_desenho']).strip()
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == desenho_alvo]
        
        if not filtro.empty:
            ferramentas_str = str(filtro['ferramentas_necessarias'].values[0])
            ferramentas = [f.strip().lower() for f in ferramentas_str.split(',')]
            
            df_tempos_clean = df_tempos.copy()
            df_tempos_clean['nome_ferramenta_lower'] = df_tempos_clean['nome_ferramenta'].str.lower()
            tempo_setup = df_tempos_clean
