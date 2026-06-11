import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 Sequenciamento - Restauração")

sec = st.secrets
url = sec["SUPABASE_URL"]
key = sec["SUPABASE_KEY"]
client = create_client(url, key)


@st.cache_data(ttl=300)
def carregar_dados():
    t_tbl = client.table("tabela_tempos")
    t_data = t_tbl.select("*").execute().data
    d_tbl = client.table("tabela_desenhos")
    d_data = d_tbl.select("*").execute().data
    return pd.DataFrame(t_data), pd.DataFrame(d_data)


df_tempos, df_desenhos = carregar_dados()


def limpar_tempo(val):
    if hasattr(val, "hour") and hasattr(val, "minute"):
        return val.hour * 60 + val.minute + (val.second / 60.0)
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            parts = [float(x) for x in val.split(":")]
            if len(parts) == 3:
                return parts[0] * 60 + parts[1] + (parts[2] / 60.0)
            if len(parts) == 2:
                return parts[0] + (parts[1] / 60.0)
            if len(parts) == 1:
                return parts[0]
        except:
            return 0.0
    return 0.0


def calcular_fim_normal(ini, mins):
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


menu_options = ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"]
menu = st.sidebar.radio("Navegação", menu_options)

if menu == "🚀 Sequenciamento":
    up = st.file_uploader("Planilha", type=["xlsx", "csv"])
    if up:
        df_raw = pd.read_excel(up)
        df_raw.columns = [c.strip() for c in df_raw.columns]
