import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

# Globais curtas para evitar cortes
MA = "Mês/Ano"
TH = "Total (Horas)"
SD = "Saldo Disponível"
HD = "Horas Disponíveis"
SU = "setup (min)"
TUM = "tempo unitário (min)"
DE = "data de entrega"
STT = "Status"
INI = "Início"
FIM = "Fim"
MAQ = "Máquina"

st.set_page_config(
    page_title="PCP",
    layout="wide",
)

sec = st.secrets
supabase = create_client(
    sec["SUPABASE_URL"],
    sec["SUPABASE_KEY"],
)


@st.cache_data(ttl=300)
def carregar_dados():
    t_res = (
        supabase.table(
            "tabela_tempos"
        )
        .select("*")
        .execute()
    )
    d_res = (
        supabase.table(
            "tabela_desenhos"
        )
        .select("*")
        .execute()
    )
    return pd.DataFrame(
        t_res.data
    ), pd.DataFrame(d_res.data)


df_tempos, df_desenhos = (
    carregar_dados()
)


def limpar_tempo(val):
    if hasattr(
        val, "hour"
    ) and hasattr(val, "minute"):
        return (
            val.hour * 60
            + val.minute
            + (val.second / 60.0)
        )
    if isinstance(
        val, (int, float)
    ):
        return float(val)
    if isinstance(val, str):
        try:
            parts = [
                float(x)
                for x in val.split(
                    ":"
                )
            ]
            if len(parts) == 3:
                return (
                    parts[0] * 60
                    + parts[1]
                    + (
                        parts[2]
                        / 60.0
                    )
                )
            elif len(parts) == 2:
                return parts[0] + (
                    parts[1] / 60.0
                )
            elif len(parts) == 1:
                return parts[0]
        except:
            return 0.0
    return 0.0


def calcular_fim_normal(
    ini, mins
):
    data = ini
    rest = mins
    while rest > 0:
        if rest <= 450:
            rest = 0
        else:
            rest -= 450
            data += (
                datetime
                .timedelta(
                    days=1
                )
            )
            while (
                data.weekday()
                >= 5
            ):
                data += (
                    datetime
                    .timedelta(
                        days=1
                    )
                )
    return data


opts = [
    "🚀 Sequenciamento",
    "🔧 Tabela Tempos",
    "📐 Tabela Desenhos",
]
menu = st.sidebar.radio(
    "Navegação", opts
)

if menu == "🚀 Sequenciamento":
    st.title(
        "🚀 Sequenciamento"
    )
    up = st.file_uploader(
        "Planilha",
        type=["xlsx", "csv"],
    )

    if up:
        check = False
        if (
            "df_pcp"
            not in
            st.session_state
        ):
            check = True
        elif (
            "f_name"
            not in
            st.session_state
        ):
            check = True
        elif (
            st.session
