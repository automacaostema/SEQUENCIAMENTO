import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

def invalidar_cache():
    st.cache_data.clear()

sec = st.secrets
url = sec["SUPABASE_URL"]
key = sec["SUPABASE_KEY"]
client = create_client(url, key)

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        t_tbl = client.table("tabela_tempos")
        d_tbl = client.table("tabela_desenhos")
        t_data = t_tbl.select("*").execute().data
        d_data = d_tbl.select("*").execute().data
        return pd.DataFrame(t_data), pd.DataFrame(d_data)
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_tempos, df_desenhos = carregar_dados()

def limpar_tempo(val):
    if hasattr(val, "hour"): return val.hour * 60 + val.minute
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        try:
            p = [float(x) for x in val.split(":")]
            if len(p) == 3: return p[0] * 60 + p[1] + (p[2] / 60.0)
            if len(p) == 2: return p[0] + (p[1] / 60.0)
            if len(p) == 1: return p[0]
        except: return 0.0
    return 0.0

def fim_norm(ini, mins):
    data = ini
    rest = mins
    while rest > 0:
        if rest <= 450: rest = 0
        else:
            rest -= 450
            data += dt.timedelta(days=1)
            while data.weekday() >= 5: data += dt.timedelta(days=1)
    return data

def calc_setup(cod):
    if df_desenhos.empty:
        return 0.0, "sem_ferramenta"
    c_str = str(cod).strip()
    nd = df_desenhos["numero_desenho"]
    mask = nd.astype(str).str.strip() == c_str
    f = df_desenhos[mask]
    if f.empty:
        return 0.0, "sem_ferramenta"
    f_v = f["ferramentas_necessarias"].values[0]
    f_str = str(f_v)
    tot = 0.0
    for ft in f_str.split(","):
        fl = ft.strip().lower()
        nf = df_tempos["nome_ferramenta"]
        m_t = nf.str.lower() == fl
        tot += df_tempos[m_t]["tempo_montagem"].sum()
    return tot, f_str

# Sidebar
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

if menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    df_t_ed = st.data_editor(df_tempos, use_container_width=True, num_rows="dynamic")
    if st.button("💾 Atualizar Banco (Tempos)"):
        dict_t = df_t_ed.to_dict(orient="records")
        client.table("tabela_tempos").upsert(dict_t).execute()
        invalidar_cache()
        st.success("Banco de Tempos Atualizado!")
        st.rerun()

elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    df_d_ed = st.data_editor(df_desenhos, use_container_width=True, num_rows="dynamic")
    if st.button("💾 Atualizar Banco (Desenhos)"):
        dict_d = df_d_ed.to_dict(orient="records")
        client.table("tabela
