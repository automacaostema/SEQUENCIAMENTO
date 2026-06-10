import streamlit as st
import pandas as pd
from supabase import create_client
import datetime

st.set_page_config(layout="wide")
st.title("🚀 Sequenciamento PCP - Corrigido")

try:
    s = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    t_df = pd.DataFrame(s.table("tabela_tempos").select("*").execute().data)
    d_df = pd.DataFrame(s.table("tabela_desenhos").select("*").execute().data)
except Exception as e:
    st.error(f"Erro Conexão: {e}")
    st.stop()

def para_minutos(val):
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, datetime.time): return val.hour * 60 + val.minute
    if isinstance(val, str):
        try:
            p = [int(x) for x in val.split(':')]
            return p[0]*60 + p[1]
        except: return 0.0
    return 0.0

up = st.file_uploader("Upload Planilha")
if up:
    df = pd.read_excel(up)
    
    def get_f(cod):
        f = d_df[d_df['numero_desenho'].astype(str).str.strip()==str(cod).strip()]
        return str(f['ferramentas_necessarias'].values[0]) if not f.empty else "sem"
    
    df['ferramental_grupo'] = df['codigo interno'].apply(get_f)
    m_list = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
    a = {n: {"data": datetime.date.today(), "ferramentas": set()} for n in m_list}
    
    res = []
    for i in range(len(df)):
        r = df.iloc[i]
        f_s = str(r['ferramental_grupo'])
        g = "Torno GL 170G" if ("Ø8" in f_s or "Ø9" in f_s) else "Torno Centur"
        maq = f"{g} - 1" if a[f"{g} - 1"]["data"] <= a[f"{g} - 2"]["data"] else f"{g} - 2"
        
        f_atuais = set(f.strip().lower() for f in f_s.split(',') if f.strip() and f_s != "sem")
        f_novas = f_atuais - a[maq]["ferramentas"]
        
        setup = sum([t_df[t_df['nome_ferramenta'].str.lower()==f]['tempo_montagem'].sum() for f in f_novas]) if f_novas else 0
        
        # Conversão garantida
        t_unit = para_minutos(r['tempo unidade'])
        total = setup + (t_unit * float(r['quantidade']))
        
        fim = a[maq]["data"] + datetime.timedelta(minutes=total)
        a[maq].update({"data": fim, "ferramentas": f_atuais})
        
        res.append({"Máquina": maq, "Setup (min)": setup, "Total (min)": total, **r})
    
    st.dataframe(pd.DataFrame(res))
