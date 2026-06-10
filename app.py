import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime

st.set_page_config(layout="wide")
st.title("🚀 Sequenciamento PCP")

# Conexão
try:
    s = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    t_df = pd.DataFrame(s.table("tabela_tempos").select("*").execute().data)
    d_df = pd.DataFrame(s.table("tabela_desenhos").select("*").execute().data)
except:
    st.error("Erro Conexão")
    st.stop()

# Funções
def para_min(v):
    if isinstance(v, (int, float)): return float(v)
    if isinstance(v, str):
        try:
            p = [int(x) for x in v.split(':')]
            return p[0]*60 + p[1]
        except: return 0.0
    return 0.0

def calc_fim(ini, mins):
    data = ini
    rest = mins
    while rest > 0:
        if rest <= 450: rest = 0
        else:
            rest -= 450
            data += datetime.timedelta(days=1)
            while data.weekday() >= 5: data += datetime.timedelta(days=1)
    return data

# Interface
up = st.file_uploader("Upload Planilha")
if up:
    df = pd.read_excel(up)
    df.columns = [c.strip() for c in df.columns]
    
    def get_f(cod):
        mask = d_df['numero_desenho'].astype(str).str.strip() == str(cod).strip()
        f = d_df[mask]
        return str(f['ferramentas_necessarias'].values[0]) if not f.empty else "sem"
    
    df['ferramental_grupo'] = df['codigo interno'].apply(get_f)
    df = df.sort_values(by=['data de entrega', 'ferramental_grupo'])
    
    m_list = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
    
    # Dicionário simplificado
    a = {}
    p_v = {}
    for n in m_list:
        a[n] = {"data": datetime.date.
