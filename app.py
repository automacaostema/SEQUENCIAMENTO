import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime

st.set_page_config(layout="wide")
st.title("🚀 Sequenciamento PCP - Setup Inteligente")

# 1. Conexão
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    t_df = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    d_df = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
except Exception as e:
    st.error(f"Erro Conexão: {e}")
    st.stop()

# 2. Funções
def para_minutos(val):
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, datetime.time): return val.hour * 60 + val.minute
    if isinstance(val, str):
        try:
            p = [int(x) for x in val.split(':')]
            return p[0]*60 + p[1]
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

# 3. Processamento
uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [c.strip() for c in df.columns]
    
    def get_f(cod):
        f = d_df[d_df['numero_desenho'].astype(str).str.strip() == str(cod).strip()]
        return str(f['ferramentas_necessarias'].values[0]) if not f.empty else "sem"
    
    df['ferramental_grupo'] = df['codigo interno'].apply(get_f)
    df = df.sort_values(by=['data de entrega', 'ferramental_grupo'])
    
    m_names = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
    agenda = {n: {"data": datetime.date.today(), "ferramentas": set()} for n in m_names}
    primeira_vez = {n: True for n in m_names}
    
    res = []
    for i in range(len(df)):
        r = df.iloc[i]
        f_s = str(r['ferramental_grupo'])
        g = "Torno GL 170G" if ("Ø8" in f_s or "Ø9" in f_s) else "Torno Centur"
        maq = f"{g} - 1" if agenda[f"{g} - 1"]["data"] <= agenda[f"{g} - 2"]["data"] else f"{g} - 2"
        
        f_atuais = set(f.strip().lower() for f in f_s.split(',') if f.strip
