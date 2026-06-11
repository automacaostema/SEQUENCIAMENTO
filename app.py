import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

opts = [
    "🚀 Sequenciamento",
    "🔧 Tabela Tempos",
    "📐 Tabela Desenhos",
]
menu = st.sidebar.radio("Navegação", opts)

sec = st.secrets
url = sec["SUPABASE_URL"]
key = sec["SUPABASE_KEY"]
client = create_client(url, key)


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


def calc_setup(cod, df_t, df_d):
    if df_d.empty:
        return 0.0, "sem_ferramenta"
    c_str = str(cod).strip()
    nd = df_d["numero_desenho"]
    mask = nd.astype(str).str.strip() == c_str
    f = df_d[mask]
    if f.empty:
        return 0.0, "sem_ferramenta"
    f_v = f["ferramentas_necessarias"].values[0]
    f_str = str(f_v)
    tot = 0.0
    for ft in f_str.split(","):
        fl = ft.strip().lower()
        nf = df_t["nome_ferramenta"]
        m_t = nf.str.lower() == fl
        tot += df_t[m_t]["tempo_montagem"].sum()
    return tot, f_str


if menu == "🚀 Sequenciamento":
    up = st.file_uploader("Planilha", type=["xlsx", "csv"])
    if up:
        df_tempos, df_desenhos = carregar_dados()
        ss = st.session_state
        check = False
        if "df_pcp" not in ss:
            check = True
        if ss.get("f_name") != up.name:
            check = True

        if check:
            try:
                ss["f_name"] = up.name
                df_raw = pd.read_excel(up)
                df_raw.columns = [c.strip() for c in df_raw.columns]

                req = [
                    "tempo unidade",
                    "quantidade",
                    "codigo interno",
                    "data de entrega",
                ]
                missing = [c for c in req if c not in df_raw.columns]
                
                if missing:
                    st.error(f"Faltam colunas: {missing}")
                else:
                    t_uni = df_raw["tempo unidade"].apply(limpar_tempo)
                    df_raw["tempo unitário (min)"] = t_uni

                    q_col = df_raw["quantidade"]
                    q_num = pd.to_numeric(q_col, errors="coerce")
                    df_raw["quantidade"] = q_num.fillna(0)

                    setups = []
                    grupos = []
                    for cod in df_raw["codigo interno"]:
                        s_m, g_f = calc_setup(cod, df_tempos, df_desenhos)
                        setups.append(s_m)
                        grupos.append(g_f)
                    
                    df_raw["setup (min)"] = setups
                    df_raw["ferramental_grupo"] = grupos

                    by_cols = ["data de entrega", "ferramental_grupo"]
                    df_raw = df_raw.sort_values(by=by_cols).copy()
                    df_raw["Ordem"] = range(1, len(df_raw) + 1)
                    ss["df_pcp"] = df_raw
            except Exception as e:
                st.error(f"Erro no Excel: {e}")

        if "df_pcp" in ss:
            st.write("### ✏️ Sequenciamento Manual")
            dis_cols = [c for c in ss["df_pcp"].columns if c != "Ordem"]

            df_editado = st.data_editor(
                data=ss["df_pcp"],
                disabled=dis_cols,
                use_container_width=True,
                key="editor_pcp",
            )

            df_seq = df_editado.sort_values(by="Ordem").copy()
            today = dt.date.today()

            m_list = [
                "Torno GL 170G - 1",
                "Torno GL 170G - 2",
                "Torno Centur - 1",
                "Torno Centur - 2",
            ]

            agenda = {}
            for m in m_list:
                agenda[m] = {"data": today, "ferramental": ""}

            maq_aloc, d_ini, d_fim, st_ent, set_reais, h_tot = (
                [], [], [], [], [], []
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
                fi_m2 = fim_norm(st_m2, mi_m2)

                if fi_m1 <= fi_m2:
                    maq_ch, st_date, ed_date, se_at, mi_fi = m1, st_m1, fi_m1, se_m1, mi_m1
                else:
                    maq_ch, st_date, ed_date, se_at, mi_fi = m2, st_m2, fi_m2, se_m2, mi_m2

                lim = pd.to_datetime(r["data de entrega"]).date()
                if ed_date <= lim:
                    status = "✅ No Prazo"
                elif lim >= today:
                    status = "⚡ No Prazo (Sobrecarga)"
                else:
                    status = "⚠️ ATRASADO (Vencido)"

                agenda[maq_ch]["data"] = ed_date
                agenda[maq_ch]["ferramental"] = fg

                maq_aloc.append(maq_ch)
                d_ini.append(st_date)
                d_fim.append(ed_date)
                st_ent.append(status)
                set_reais.append(se_at)
                h_tot.append(round(mi_fi / 60, 2))

            df_seq["Máquina"] = maq_aloc
            df_seq["Início"] = d_ini
            df_seq["Fim"] = d_fim
            df_seq["Status"] = st_ent
            df_seq["setup (min)"] = set_reais
            df_seq["Total (Horas)"] = h_tot

            f_dt = pd.to_datetime(df_seq["Fim"])
            df_seq["Mês/Ano"] = f_dt.dt.to_period("M").astype(str)

            df_mes = df_seq.groupby(["Mês/Ano", "Máquina"])["Total (Horas)"].sum().reset_index()
            df_mes["Horas Disponíveis"] = 157.5

            h_dis = df_mes["Horas Disponíveis"]
            t_hrs = df_mes["Total (Horas)"]
            diff = h_dis - t_hrs
            df_mes["Saldo Disponível"] = diff.clip(lower=0)

            st.write("## 📊 Ocupação Real")

            fig = px.bar(
                data_frame=df_mes,
                x="Mês/Ano",
                y=["Total (Horas)", "Saldo Disponível"],
                facet_col="Máquina",
                facet_col_wrap=2,
                title="Horas",
                barmode="stack",
            )
            st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.write("## 🗓️ Filas de Trabalho")
            abas = st.tabs(m_list)

            for i, maq in enumerate(m_list):
                with abas[i]:
                    mask_m = df_seq["Máquina"] == maq
                    df_m = df_seq[mask_m]

                    df_m = df_m.drop(columns=["Máquina", "Mês/Ano"])
                    f_cols = ["Status", "Início", "Fim", "data de entrega", "Total (Horas)", "setup (min)"]

                    cols = list(f_cols)
                    for c in df_m.columns:
                        if c not in f_cols:
                            cols.append(c)
                    st.dataframe(df_m[cols], use_container_width=True)

elif menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    df_tempos, _ = carregar_dados()
    if df_tempos.empty:
        st.error("Não foi possível carregar os dados.")
    else:
        df_t_ed = st.data_editor(
            df_tempos,
            use_container_width=True,
            num_rows="dynamic",
            key="edit_tempos_db",
        )
        if st.button("💾 Atualizar Banco (Tempos)"):
            dict_t = []
            for r in df_t_ed.to_dict(orient="records"):
                limpo = {k: (v if pd.notna(v) else None) for k, v in r.items()}
                if "id" in limpo and limpo["id"] is None:
                    del limpo["id"]
                dict_t.append(limpo)

            client.table("tabela_tempos").upsert(dict_t).execute()
            st.success("Banco de Tempos Atualizado!")

elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    _, df_desenhos = carregar_dados()
    if df_desenhos.empty:
        st.error("Não foi possível carregar os dados.")
    else:
        df_d_ed = st.data_editor(
            df_desenhos,
            use_container_width=True,
            num_rows="dynamic",
            key="edit_desenhos_db",
        )
        if st.button("💾 Atualizar Banco (Desenhos)"):
            dict_d = []
            for r in df_d_ed.to_dict(orient="records"):
                limpo = {k: (v if pd.notna(v) else None) for k, v in r.items()}
                if "id" in limpo and limpo["id"] is None:
                    del limpo["id"]
                dict_d.append(limpo)

            client.table("tabela_desenhos").upsert(dict_d).execute()
            st.success("Banco de Desenhos Updated!")
