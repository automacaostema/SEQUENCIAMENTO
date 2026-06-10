import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime

st.set_page_config(layout="wide")
st.title("🚀 Sequenciamento PCP")

try:
    s = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    t_df = pd.DataFrame(s.table("tabela_tempos").select("*").execute().data)
    d_df = pd.DataFrame(s.table("tabela_desenhos").select("*").execute().data)
except Exception as e:
    st.error(f"Erro Conexão: {e}")
    st.stop()

def para_min(val):
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        try:
            p = [int(x) for x in val.split(':')]
            return p[0]*60 + p[1]
        except: return 0.0
    return 0.0

def calc_fim(ini, mins):
    data = ini
    restante = mins
    while restante > 0:
        if restante <= 450: restante = 0
        else:
            restante -= 450
            data += datetime.timedelta(days=1)
            while data.weekday() >= 5: data += datetime.timedelta(days=1)
    return data

up = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if up:
    df = pd.read_excel(up)
    df.columns = [c.strip() for c in df.columns]
    
    def get_f(cod):
        f = d_df[d_df['numero_desenho'].astype(str).str.strip() == str(cod).strip()]
        return str(f['ferramentas_necessarias'].values[0]) if not f.empty else "sem"
    
    df['ferramental_grupo'] = df['codigo interno'].apply(get_f)
    df = df.sort_values(by=['data de entrega', 'ferramental_grupo'])
    
    m_names = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
    a = {n: {"data": datetime.date.today(), "ferramentas": set()} for n in m_names}
    p_v = {n: True for n in m_names}
    
    res = []
    for i in range(len(df)):
        r = df.iloc[i]
        f_s = str(r['ferramental_grupo'])
        # Removido o caractere especial Ø
        g = "Torno GL 170G" if ("8" in f_s or "9" in f_s) else "Torno Centur"
        maq = f"{g} - 1" if a[f"{g} - 1"]["data"] <= a[f"{g} - 2"]["data"] else f"{g} - 2"
        f_atuais = set(f.strip().lower() for f in f_s.split(',') if f.strip() and f_s != "sem")
        f_novas = f_atuais if p_v[maq] else (f_atuais
