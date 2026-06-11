import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

sec = st.secrets
url = sec["SUPABASE_URL"]
key = sec["SUPABASE_KEY"]
client = create_client(url, key)


@st.cache_data(ttl=300)
def pegar_dados():
    t_tbl = client.table("tabela_tempos")
    t_d = t_tbl.select("*").execute().data
    d_tbl = client.table("tabela_desenhos")
    d_d = d_tbl.select("*").execute().data
    return pd.DataFrame(t_d), pd.DataFrame(d_d)


df_tempos, df_desenhos = pegar_dados()


def limpar_tempo(val):
    if hasattr(val, "hour") and hasattr(
        val, "minute"
    ):
        return (
            val.hour * 60
            + val.minute
            + (val.second / 60.0)
        )
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            p = [
                float(x)
                for x in val.split(":")
            ]
            if len(p) == 3:
                return (
                    p[0] * 60
                    + p[1]
                    + (p[2] / 60.0)
                )
            if len(p) == 2:
                return p[0] + (
                    p[1] / 60.0
                )
            if len(p) == 1:
                return p[0]
        except:
            return 0.0
    return 0.0


def fim_norm(ini, mins):
    d = ini
    r = mins
    while r > 0:
        if r <= 450:
            r = 0
        else:
            r -= 450
            d += dt.timedelta(days=1)
            while d.weekday() >= 5:
                d += dt.timedelta(days=1)
    return d


def pcp_page():
    up = st.file_uploader("Planilha")
    if not up:
        return

    df = pd.read_excel(up)
    cols = [
        c.strip() for c in df.columns
    ]
    df.columns = cols

    req = [
        "tempo unidade",
        "quantidade",
        "codigo interno",
        "data de entrega",
    ]
    ok = True
    for c in req:
        if c not in df.columns:
            ok = False

    if not ok:
        st.error("Colunas ausentes!")
        return

    tu = df["tempo unidade"]
    c_uni = "tempo unitário (min)"
    df[c_name] = tu.apply(limpar_tempo)

    q = df["quantidade"]
    q_n = pd.to_numeric(
        q, errors="coerce"
    )
    df["quantidade"] = q_n.fillna(0)

    def set_up(cod):
