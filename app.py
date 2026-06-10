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
    st.error(f"Erro: {e}")
    st.stop()

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

up = st.file_uploader("Upload Planilha")
if up:
    df = pd.read_excel(up)
    df.columns = [c.strip() for c in df.columns]
    
    def get_f(cod):
        f = d_df[d_df['numero_desenho'].astype(str).str.strip() == str(cod).strip()]
        return str(f['ferramentas_necessarias'].values[0]) if not f.empty else "sem"
    
    df['ferramental_grupo'] = df['codigo interno'].apply(get_f)
    df = df.sort_values(by=['data de entrega', 'ferramental_grupo'])
    
    m_list = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
    a = {n: {"data": datetime.date.today(), "ferramentas": set()} for n in m_list}
    p_v = {n: True for n in m_list}
    
    res = []
    for i in range(len(df)):
        r = df.iloc[i]
        f_s = str(r['ferramental_grupo'])
        g = "Torno GL 170G" if ("8" in f_s or "9" in f_s) else "Torno Centur"
        maq = f"{g} - 1" if a[f"{g} - 1"]["data"] <= a[f"{g} - 2"]["data"] else f"{g} - 2"
        f_atuais = set(f.strip().lower() for f in f_s.split(',') if f.strip() and f_s != "sem")
        
        if p_v[maq]:
            f_novas = f_atuais
            p_v[maq] = False
        else:
            f_novas = f_atuais - a[maq]["ferramentas"]
            
        setup = sum([t_df[t_df['nome_ferramenta'].str.lower()==f]['tempo_montagem'].sum() for f in f_novas]) if f_novas else 0
        total = setup + (para_min(r['tempo unidade']) * float(r['quantidade']))
        fim = calc_fim(a[maq]["data"], total)
        a[maq].update({"data": fim, "ferramentas": f_atuais})
        res.append({"Máquina": maq, "Total": round(total/60, 2), "Setup": setup, **r})
    
    st.dataframe(pd.DataFrame(res))
