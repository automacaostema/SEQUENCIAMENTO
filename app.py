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
def carregar_dados():
    t_tbl = client.table("tabela_tempos")
    d_tbl = client.table("tabela_desenhos")
    t_data = t_tbl.select("*").execute().data
    d_data = d_tbl.select("*").execute().data
    return pd.DataFrame(t_data), pd.DataFrame(d_data)


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


opts = ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"]
menu = st.sidebar.radio("Navegação", opts)

if menu == "🚀 Sequenciamento":
    up = st.file_uploader("Planilha", type=["xlsx", "csv"])
    if up:
        ss = st.session_state
        check = False
        if "df_pcp" not in ss:
            check = True
        if "f_name" not in ss:
            check = True
        if ss.get("f_name") != up.name:
            check = True

        if check:
            ss["f_name"] = up.name
            df_raw = pd.read_excel(up)
            df_raw.columns = [c.strip() for c in df_raw.columns]

            t_uni = df_raw["tempo unidade"].apply(limpar_tempo)
            df_raw["tempo unitário (min)"] = t_uni

            q_col = df_raw["quantidade"]
            q_num = pd.to_numeric(q_col, errors="coerce")
            df_raw["quantidade"] = q_num.fillna(0)

            def calc_setup(cod):
                c_str = str(cod).strip()
                nd = df_desenhos["numero_desenho"]
                mask = nd.astype(str).str.strip() == c_str
                f = df_desenhos[mask]
                if not f.empty:
                    f_v = f["ferramentas_necessarias"].values[0]
                    f_str = str(f_v)
                    tot = 0.0
                    for ft in f_str.split(","):
                        fl = ft.strip().lower()
                        nf = df_tempos["nome_ferramenta"]
                        m_t = nf.str.lower() == fl
                        tot += df_tempos[m_t]["tempo_montagem"].sum()
                    return tot, f_str
                return 0.0, "sem_ferramenta"

            res = df_raw["codigo interno"].apply(calc_setup)
            df_raw["setup (min)"], df_raw["ferramental_grupo"] = zip(
                *res
            )

            by_cols = ["data de entrega", "ferramental_grupo"]
            df_raw = df_raw.sort_values(by=by_cols).copy()
            df_raw["Ordem"] = range(1, len(df_raw) + 1)
            ss["df_pcp"] = df_raw

        st.write("### ✏️ Sequenciamento Manual")

        dis_cols = []
        for c in ss["df_pcp"].columns:
            if c != "Ordem":
                dis_cols.append(c)

        ed_args = {}
        ed_args["data_frame"] = ss["df_pcp"]
        ed_args["disabled"] = dis_cols
        ed_args["use_container_width"] = True
        ed_args["key"] = "editor_pcp"

        df_editado = st.data_editor(**ed_args)
        df_seq = df_editado.sort_values(by=["Ordem"]).copy()
        today = dt.date.today()

        m_list = [
            "Torno GL 170G - 1",
            "Torno GL 170G - 2",
            "Torno Centur - 1",
            "Torno Centur - 2",
        ]

        agenda = {}
        agenda["Torno GL 170G - 1"] = {"data": today, "ferramental": ""}
        agenda["Torno GL 170G - 2"] = {"data": today, "ferramental": ""}
        agenda["Torno Centur - 1"] = {"data": today, "ferramental": ""}
        agenda["Torno Centur - 2"] = {"data": today, "ferramental": ""}

        maq_aloc, d_ini, d_fim, st_ent, set_reais, h_tot = (
            [],
            [],
            [],
            [],
            [],
            [],
        )
        items = df_seq.to_dict("records")

        for r in items:
            fg = str(r["ferramental_grupo"])
            is_gl = "8" in fg or "9" in fg
            g_maq = "Torno GL 170G" if is_gl else "Torno Centur"
            m1 = f"{g_maq} - 1"
            m2 = f"{g_maq} - 2"

            st_m1 = max(today, agenda[m1]["data"])
            se_m1 = float(r["setup (min)"])
            if agenda[m1]["ferramental"] == fg:
                se_m1 = 0.0
            t_u = r["tempo unitário (min)"]
            mi_m1 = se_m1 + (t_u * r["quantidade"])
            fi_m1 = fim_norm(st_m1, mi_m1)

            st_m2 = max(today, agenda[m2]["data"])
            se_m2 = float(r["setup (min)"])
            if agenda[m2]["ferramental"] == fg:
                se_m2 = 0.0
            mi_m2 = se_m2 + (t_u * r["quantidade"])
