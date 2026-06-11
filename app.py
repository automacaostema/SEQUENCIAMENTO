import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="PCP", layout="wide"
)

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


opts = [
    "🚀 Sequenciamento",
    "🔧 Tabela Tempos",
    "📐 Tabela Desenhos",
]
menu = st.sidebar.radio(
    "Navegação", opts
)

if menu == "🚀 Sequenciamento":
    st.title("🚀 Sequenciamento Otimizado")
    up = st.file_uploader(
        "Planilha", type=["xlsx", "csv"]
    )

    if up:
        check = False
        if "df_pcp" not in st.session_state:
            check = True
        elif "f_name" not in st.session_state:
            check = True
        elif (
            st.session_state.f_name
            != up.name
        ):
            check = True

        if check:
            st.session_state.f_name = (
                up.name
            )
            df_raw = pd.read_excel(up)
            
            # Limpeza plana de colunas
            new_cols = []
            for c in df_raw.columns:
                new_cols.append(c.strip())
            df_raw.columns = new_cols

            tu_col = df_raw["tempo unidade"]
            t_min = tu_col.apply(limpar_tempo)
            df_raw["tempo unitário (min)"] = t_min
            
            q_col = df_raw["quantidade"]
            q_num = pd.to_numeric(
                q_col, errors="coerce"
            )
            df_raw["quantidade"] = q_num.fillna(0)

            def calcular_setup(cod):
                c_str = str(cod).strip()
                mask = (
                    df_desenhos[
                        "numero_desenho"
                    ]
                    .astype(str)
                    .str.strip()
                    == c_str
                )
                filtro = df_desenhos[mask]
                if not filtro.empty:
                    f_str = str(
                        filtro[
                            "ferramentas_necessarias"
                        ].values[0]
                    )
                    total = 0.0
                    for f in f_str.split(
                        ","
                    ):
                        fl = f.strip().lower()
                        m_t = (
                            df_tempos[
                                "nome_ferramenta"
                            ].str.lower()
                            == fl
                        )
                        total += df_tempos[
                            m_t
                        ][
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
            
            by_cols = [
                "data de entrega",
                "ferramental_grupo",
            ]
            df_raw = df_raw.sort_values(
                by=by_cols
            ).copy()
            df_raw["Ordem"] = range(
                1, len(df_raw) + 1
            )
            st.session_state.df_pcp = (
                df_raw
            )

        st.write(
            "### ✏️ Sequenciamento Manual"
        )

        dis_cols = []
        for c in st.session_state.df_pcp.columns:
            if c != "Ordem":
                dis_cols.append(c)

        df_editado = st.data_editor(
            st.session_state.df_pcp,
            disabled=dis_cols,
            use_container_width=True,
            key="editor_pcp",
        )
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
        agenda["Torno GL 170G - 1"] = {
            "data": today,
            "ferramental": "",
        }
        agenda["Torno GL 170G - 2"] = {
            "data": today,
            "ferramental": "",
        }
        agenda["Torno Centur - 1"] = {
            "data": today,
            "ferramental": "",
        }
        agenda["Torno Centur - 2"] = {
            "data": today,
            "ferramental": "",
        }

        (
            maq_aloc,
            d_ini,
            d_fim,
            st_ent,
            set_reais,
            h_tot,
        ) = ([], [], [], [], [], [])
        lista_itens = df_seq.to_dict(
            "records"
        )

        for r in lista_itens:
            fg_str = str(
                r["ferramental_grupo"]
            )
            is_gl = (
                "8" in fg_str
                or "9" in fg_str
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
                    r["setup (min)"]
                )
            )
            min_m1 = set_m1 + (
                r["tempo unitário (min)"]
                * r["quantidade"]
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
                    r["setup (min)"]
                )
            )
            min_m2 = set_m2 + (
                r["tempo unitário (min)"]
                * r["quantidade"]
            )
            fim_m2 = calcular_fim_normal(
                st_m2, min_m2
            )

            if fim_m1 <= fim_m2:
                (
                    maq_ch,
                    st_date,
                    ed_date,
                    se_at,
                    mi_fi,
                ) = (
                    m1,
                    st_m1,
                    fim_m1,
                    set_m1,
                    min_m1,
                )
            else:
                (
                    maq_ch,
                    st_date,
                    ed_date,
                    se_at,
                    mi_fi,
                ) = (
                    m2,
                    st_m2,
                    fim_m2,
                    set_m2,
                    min_m2,
                )

            lim = pd.to_datetime(
                r["data de entrega"]
            ).date()
            if ed_date <= lim:
                status = "✅ No Prazo"
            elif lim >= today:
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

            maq_aloc.append(maq_ch)
            d_ini.append(st_date)
            d_fim.append(ed_date)
            st_ent.append(status)
            set_reais.append(se_at)
            h_tot.append(
                round(mi_fi / 60, 2)
            )

        df_seq["Máquina"] = maq_aloc
        df_seq["Início"] = d_ini
        df_seq["Fim"] = d_fim
        df_seq["Status"] = st_ent
        df_seq["setup (min)"] = set_reais
        df_seq["Total (Horas)"] = h_tot

        df_seq["Mês/Ano"] = (
            pd.to_datetime(df_seq["Fim"])
            .dt.to_period("M")
            .astype(str)
        )
        
        by_g = ["Mês/Ano", "Máquina"]
        df_mes = (
            df_seq.groupby(by_g)[
                "Total (Horas)"
            ].sum().reset_index()
        )
        df_mes["Horas Disponíveis"] = 157.5
        
        h_disp = df_mes["Horas Disponíveis"]
        t_hrs = df_mes["Total (Horas)"]
        df_mes["Saldo Disponível"] = (
            (h_disp - t_hrs).clip(lower=0)
        )

        st.write("## 📊 Ocupação Real")

        fig_args = {}
        fig_args["data_frame"] = df_mes
        fig_args["x"] = "Mês/Ano
