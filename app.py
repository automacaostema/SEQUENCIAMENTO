import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 Sequenciamento Otimizado")

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

        # Verificador de colunas obrigatórias
        req = [
            "tempo unidade",
            "quantidade",
            "codigo interno",
            "data de entrega",
        ]
        erros = [c for c in req if c not in df_raw.columns]

        if erros:
            st.error(f"❌ Colunas ausentes no Excel: {erros}")
            st.write("⚠️ Colunas encontradas no seu arquivo:")
            st.write(list(df_raw.columns))
        else:
            t_uni = df_raw["tempo unidade"].apply(limpar_tempo)
            df_raw["tempo unitário (min)"] = t_uni

            qtd = df_raw["quantidade"]
            qtd_num = pd.to_numeric(qtd, errors="coerce")
            df_raw["quantidade"] = qtd_num.fillna(0)

            def calcular_setup(cod):
                c_str = str(cod).strip()
                des_num = df_desenhos["numero_desenho"]
                mask = des_num.astype(str).str.strip() == c_str
                filtro = df_desenhos[mask]
                if not filtro.empty:
                    f_val = filtro["ferramentas_necessarias"].values[0]
                    f_str = str(f_val)
                    total = 0.0
                    for f in f_str.split(","):
                        fl = f.strip().lower()
                        t_name = df_tempos["nome_ferramenta"]
                        m_t = t_name.str.lower() == fl
                        total += df_tempos[m_t]["tempo_montagem"].sum()
                    return total, f_str
                return 0.0, "sem_ferramenta"

            res_setup = df_raw["codigo interno"].apply(calcular_setup)
            df_raw["setup (min)"], df_raw["ferramental_grupo"] = zip(*res_setup)

            sort_cols = ["data de entrega", "ferramental_grupo"]
            df_seq = df_raw.sort_values(by=
