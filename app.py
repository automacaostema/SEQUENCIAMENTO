import streamlit as st
import pandas as pd
from supabase import create_client
import datetime

st.set_page_config(layout="wide")
try:
    s = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    t_data = s.table("tabela_tempos").select("*").execute().data
    d_data = s.table("tabela_desenhos").select("*").execute().data
    t_df, d_df = pd.DataFrame(t_data), pd.DataFrame(d_data)
except:
    st.error("Erro Conexão")
    st.stop()

up = st.file_uploader("Upload")
if up:
    df = pd.read_excel(up)
    def get_f(cod):
        f = d_df[d_df['numero_desenho'].astype(str).str.strip()==str(cod).strip()]
        return str(f['ferramentas_necessarias'].values[0]) if not f.empty else "sem"
    
    df['ferramental_grupo'] = df['codigo interno'].apply(get_f)
    m = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
    a = {n: {"data": datetime.date.today(), "ferramentas": set()} for n in m}
    res = []
    for i in range(len(df)):
        r = df.iloc[i]
        f_s = str(r['ferramental_grupo'])
        g = "Torno GL 170G" if ("Ø8" in f_s or "Ø9" in f_s) else "Torno Centur"
        maq = f"{g} - 1" if a[f"{g} - 1"]["data"] <= a[f"{g} - 2"]["data"] else f"{g} - 2"
        f_atuais = set(f.strip().lower() for f in f_s.split(',') if f.strip() and f_s != "sem")
        f_novas = f_atuais - a[maq]["ferramentas"]
        setup = sum([t_df[t_df['nome_ferramenta'].str.lower()==f]['tempo_montagem'].sum() for f in f_novas]) if f_novas else 0
        total = setup + (r['tempo unidade'] * r['quantidade'])
        fim = datetime.date.today() + datetime.timedelta(days=total/450)
        a[maq].update({"data": fim, "ferramentas": f_atuais})
        res.append({"Máquina": maq, "Setup": setup, "Total": total, **r})
    
    st.dataframe(pd.DataFrame(res))
