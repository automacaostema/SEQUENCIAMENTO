import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime

st.set_page_config(
    page_title="Sistema Stema - PCP", layout="wide"
)
st.title("🚀 Sequenciamento Otimizado - Stema")

sec = st.secrets
supabase = create_client(
    sec["SUPABASE_URL"], sec["SUPABASE_KEY"]
)


@st.cache_data(ttl=300)
def carregar_dados():
    t_res = supabase.table("tabela_tempos").select("*").execute()
    d_res = supabase.table("tabela_desenhos").select("*").execute()
    return pd.DataFrame(t_res.data), pd.DataFrame(d_res.data)


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
                return (
                    parts[0] * 60 + parts[1] + (parts[2] / 60.0)
                )
            elif len(parts) == 2:
                return parts[0] + (parts[1] / 60.0)
            elif len(parts) == 1:
                return parts[0]
        except:
            return 0.0
    return 0.0


def calcular_fim_normal(data_inicio, minutos_totais):
    data = data_inicio
    tempo_restante = minutos_totais
    while tempo_restante > 0:
        if tempo_restante <= 450:
            tempo_restante = 0
        else:
            tempo_restante -= 450
            data += datetime.timedelta(days=1)
            while data.weekday() >= 5:
                data += datetime.timedelta(days=1)
    return data


uploaded_file = st.file_uploader(
    "Suba a planilha do PCP", type=["xlsx", "csv"]
)

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    df_pcp.columns = [c.strip() for c in df_pcp.columns]

    df_pcp["tempo unitário (min)"] = df_pcp["tempo unidade"].apply(
        limpar_tempo
    )
    df_pcp["quantidade"] = pd.to_numeric(
        df_pcp["quantidade"], errors="coerce"
    ).fillna(0)

    def calcular_setup(cod):
        cod_str = str(cod).strip()
        d_df = df_desenhos
        mask_des = (
            d_df["numero_desenho"].astype(str).str.strip()
            == cod_str
        )
        filtro = d_df[mask_des]
        if not filtro.empty:
            ferr_str = str(
                filtro["ferramentas_necessarias"].values[0]
            )
            ferramentas = ferr_str.split(",")
            total = 0.0
            for f in ferramentas:
                f_l = f.strip().lower()
                t_f = df_tempos
                mask = t_f["nome_ferramenta"].str.lower() == f_l
                total += t_f[mask]["tempo_montagem"].sum()
            return total, ferr_str
        return 0.0, "sem_ferramenta"

    resultados = df_pcp["codigo interno"].apply(calcular_setup)
    (
        df_pcp["setup (min)"],
        df_pcp["ferramental_grupo"],
    ) = zip(*resultados)

    df_sequenciado = df_pcp.sort_values(
        by=["data de entrega", "ferramental_grupo"]
    ).copy()

    today = datetime.date.today()
    agenda = {
        "Torno GL 170G - 1": {"data": today, "ferramental": ""},
        "Torno GL 170G - 2": {"data": today, "ferramental": ""},
        "Torno Centur -
