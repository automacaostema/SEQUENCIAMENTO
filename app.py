import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

opts = []
opts.append("🚀 Sequenciamento")
opts.append("🔧 Tabela Tempos")
opts.append("📐 Tabela Desenhos")
menu = st.sidebar.radio("Navegação", opts)

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
        st.error("Erro de conexão!")
        return pd.DataFrame(), pd.DataFrame()


df_tempos, df_desenhos = carregar_dados()


def limpar_tempo(val):
    if hasattr(val, "hour"):
        return val.hour * 60 + val.minute
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            p = [float(x) for x in val.split(":")]
            if len(p) == 3:
                return p[0] * 60 + p[1] + (p[2] / 60.0)
            if len(p) == 2:
                return p[0] + (p[1] / 60.0)
            if len(p) == 1:
                return p[0]
        except:
            return 0.0
    return 0.0


def fim_norm(ini, mins):
    data = ini
    rest = mins
    while rest > 0:
        if rest <= 450:
            rest = 0
        else:
            rest -= 450
            data += dt.timedelta(days=1)
            while data.weekday() >= 5:
                data += dt.timedelta(days=1)
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
    tot = 0.
