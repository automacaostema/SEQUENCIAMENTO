import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="PCP", layout="wide"
)
st.title("🚀 Sequenciamento Otimizado")

sec = st.secrets
supabase = create_client(
    sec["SUPABASE_URL"],
    sec["SUPABASE_KEY"],
)


@st.cache_data(ttl=300)
def carregar_dados():
    t_res = (
        supabase.table("tabela_tempos")
        .select("*")
        .execute()
    )
    d_res = (
        supabase.table("tabela_desenhos")
        .select("*")
        .execute()
    )
    return pd.DataFrame(
        t_res.data
    ), pd.DataFrame(d_res.data)


df_tempos, df_desenhos = carregar_dados()


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
            parts = [
                float(x)
                for x in val.split(":")
            ]
            if len(parts) == 3:
                return (
                    parts[0] * 60
                    + parts[1]
                    + (parts[2] / 60.0)
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


def calcular_fim_normal(ini, mins):
    data = ini
    rest = mins
    while rest > 0:
        if rest <= 450:
            rest = 0
        else:
            rest -= 450
            data += datetime.timedelta(
                days=1
            )
            while data.weekday() >= 5:
                data += datetime.timedelta(
                    days=1
                )
    return data


up = st.file_uploader(
    "Planilha", type=["xlsx", "csv"]
)

if up:
    # Memória para não resetar no clique
    if (
        "f_name" not in st.session_state
        or st.session_state.f_name
        != up.name
    ):
        st.session_state.f_name = (
            up.name
        )
        df_raw = pd.read_excel(up)
        df_raw.columns = [
            c.strip()
            for c in df_raw.columns
        ]
        df_raw[
            "tempo unitário (min)"
        ] = df_raw[
            "tempo unidade"
        ].apply(limpar_tempo)

        df_raw["quantidade"] = (
            pd.to_numeric(
                df_raw["quantidade"],
                errors="coerce",
            ).fillna(0)
        )

        def calcular_setup(cod):
            c_str = str(cod).strip()
            d_df = df_desenhos
            mask = (
                d_df["numero_desenho"]
                .astype(str)
                .str.strip()
                == c_str
            )
            filtro = d_df[mask]
            if not filtro.empty:
                f_str = str(
                    filtro[
                        "ferramentas_necessarias"
                    ].values[0]
                )
                ferramentas = (
                    f_str.split(",")
                )
                total = 0.0
                for f in ferramentas:
                    fl = f.strip().lower()
                    t_f = df_tempos
                    m_t = (
                        t_f[
                            "nome_ferramenta"
                        ].str.lower()
                        == fl
                    )
                    total += t_f[m_t][
                        "tempo_montagem"
                    ].sum()
                return total, f_str
            return 0.0, "sem_ferramenta"

        res_setup = df_raw[
            "codigo interno"
        ].apply(calcular_setup)
        (
            df_raw["setup (min)"],
            df_raw["ferramental_grupo"],
        ) = zip(*res_setup)

        df_raw = df_raw.sort_values(
            by=[
                "data de entrega",
                "ferramental_grupo",
            ]
        ).copy()
        
        df_raw["Ordem"] = range(
            1, len(df_raw) + 1
        )
        st.session_state.df_pcp = (
            df_raw
        )

    st.write("### ✏️ Sequenciamento Manual")
    st.info(
        "Altere os números da coluna "
        "'Ordem' para recalcular."
    )
    
    # Tabela com persistência de dados
    df_editado = st.data_editor(
        st.session_state.df_pcp,
        disabled=[
            c
            for c in st.session_state
            .df_pcp.columns
            if c != "Ordem"
        ],
        use_container_width=True,
    )
    st.session_state.df_pcp = (
        df_editado
    )

    # Reordena baseado no que você digitou
    df_seq = df_editado.sort_values(
        by=["Ordem"]
    ).copy()

    today = datetime.date.today()

    m_list = [
        "Torno GL 170G - 1",
        "Torno GL 170G - 2",
        "Torno Centur - 1",
        "Torno Centur - 2",
    ]

    agenda = {}
    for n in m_list:
        agenda[n] = {
            "data": today,
            "ferramental": "",
        }

    maquinas_alocadas = []
    datas_inicio = []
    datas_fim = []
    status_entrega = []
    setups_reais = []
    horas_totais = []

    for idx, row in df_seq.iterrows():
        fg_str = str(
            row["ferramental_grupo"]
        )
        is_gl = (
            "8" in fg_str or "9" in fg_str
        )
        g_maq = (
            "Torno GL 170G"
            if is_gl
            else "Torno Centur"
        )
        m1 = f"{g_maq} - 1"
        m2 = f"{g_maq} - 2"

        st_m1 = max(
            today, agenda[m1]["data"]
        )
        is_same1 = (
            agenda[m1]["ferramental"]
            == fg_str
        )
        set_m1 = (
            0.0
            if is_same1
            else float(
                row["setup (min)"]
            )
        )
        min_m1 = set_m1 + (
            row["tempo unitário (min)"]
            * row["quantidade"]
        )
        fim_m1 = calcular_fim_normal(
            st_m1, min_m1
        )

        st_m2 = max(
            today, agenda[m2]["data"]
        )
        is_same2 = (
            agenda[m2]["ferramental"]
            == fg_str
        )
        set_m2 = (
            0.0
            if is_same2
            else float(
                row["setup (min)"]
            )
        )
        min_m2 = set_m2 + (
            row["tempo unitário (min)"]
            * row["quantidade"]
        )
        fim_m2 = calcular_fim_normal(
            st_m2, min_m2
        )

        if fim_m1 <= fim_m2:
            maq_ch = m1
            st_date = st_m1
            ed_date = fim_m1
            se_at = set_m1
            mi_fi = min_m1
        else:
            maq_ch = m2
            st_date = st_m2
            ed_date = fim_m2
            se_at = set_m2
            mi_fi = min_m2

        lim = pd.to_datetime(
            row["data de entrega"]
        ).date()

        if ed_date <= lim:
            status = "✅ No Prazo"
        else:
            if lim >= today:
                status = (
                    "⚡ No Prazo "
                    "(Com Sobrecarga)"
                )
            else:
                status = (
                    "⚠️ ATRASADO "
                    "(Prazo Vencido)"
                )

        agenda[maq_ch]["data"] = ed_date
        agenda[maq_ch][
            "ferramental"
        ] = fg_str

        maquinas_alocadas.append(maq_ch)
        datas_inicio.append(st_date)
        datas_fim.append(ed_date)
        status_entrega.append(status)
        setups_reais.append(se_at)
        horas_totais.append(
            round(mi_fi / 60, 2)
        )

    df_seq["Máquina"] = maquinas_alocadas
    df_seq["Início"] = datas_inicio
    df_seq["Fim"] = datas_fim
    df_seq["Status"] = status_entrega
    df_seq["setup (min)"] = setups_reais
    df_seq[
        "Total (Horas)"
    ] = horas_totais

    df_seq["Mês/Ano"] = (
        pd.to_datetime(df_seq["Fim"])
        .dt.to_period("M")
        .astype(str)
    )
    grp = df_seq.groupby(
