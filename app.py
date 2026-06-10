import streamlit as st
import pandas as pd
from supabase import create_client
import datetime

st.set_page_config(layout="wide")
st.title("🚀 Sequenciamento PCP - Setup Inteligente")

# 1. Configuração
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erro Supabase: {e}")

# 2. Dados
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        t = supabase.table("tabela_tempos").select("*").execute().data
        d = supabase.table("tabela_desenhos").select("*").execute().data
        return pd.DataFrame(t), pd.DataFrame(d)
    except:
        return pd.DataFrame(), pd.DataFrame()

df_tempos, df_desenhos = carregar_dados()

# 3. Funções
def limpar_tempo(v):
    try:
        if isinstance(v, (int, float)): return float(v)
        if isinstance(v, str):
            p = [float(x) for x in v.split(':')]
            return p[0]*60 + p[1] + (p[2]/60.0) if len(p)==3 else p[0] + (p[1]/60.0)
    except: return 0.0
    return 0.0

def calcular_fim(inicio, mins):
    data = inicio
    restante = mins
    while restante > 0:
        if restante <= 450: restante = 0
        else:
            restante -= 450
            data += datetime.timedelta(days=1)
            while data.weekday() >= 5: data += datetime.timedelta(days=1)
    return data

# 4. Interface e Processamento
uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [c.strip() for c in df.columns]
        df['tempo unitário (min)'] = df['tempo unidade'].apply(limpar_tempo)
        df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)

        def get_ferram
