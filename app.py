import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="PCP", layout="wide")

sec = st.secrets
supabase = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])

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
                return parts[0] * 60 + parts[1] + (parts[2] / 60.0)
            elif len(parts) == 2:
                return parts[0] + (parts[1] / 60.0)
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
            data += datetime.timedelta(days=1)
            while data.weekday() >= 5:
                data += datetime.timedelta(days=1)
    return data

menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

if menu == "🚀 Sequenciamento":
    st.title("🚀 Sequenciamento Otimizado")
    up = st.file_uploader("Planilha", type=["xlsx", "csv"])

    if up:
        if "df_pcp" not in st.session_state or "f_name" not in st.session_state or st.session_state.f_name != up.name:
            st.session_state.f_name = up.name
            df_raw = pd.read_excel(up)
            df_raw.columns = [c.strip() for c in df_raw.columns]
            df_raw["tempo unitário (min)"] = df_raw["tempo unidade"].apply(limpar_tempo)
            df_raw["quantidade"] = pd.to_numeric(df_raw["quantidade"], errors="coerce").fillna(0)

            def calcular_setup(cod):
                c_str = str(cod).strip()
                mask = df_desenhos["numero_desenho"].astype(str).str.strip() == c_str
                filtro = df_desenhos[mask]
                if not filtro.empty:
                    f_str = str(filtro["ferramentas_necessarias"].values[0])
                    total = 0.0
                    for f in f_str.split(","):
                        fl = f.strip().lower()
                        m_t = df_tempos["nome_ferramenta"].str.lower() == fl
                        total += df_tempos[m_t]["tempo_montagem"].sum()
                    return total, f_str
                return 0.0, "sem_ferramenta"

            res_setup = df_raw["codigo interno"].apply(calcular_setup)
            df_raw["setup (min)"], df_raw["ferramental_grupo"] = zip(*res_setup)
            df_raw = df_raw.sort_values(by=["data de entrega", "ferramental_grupo"]).copy()
            df_raw["Ordem"] = range(1, len(df_raw) + 1)
            st.session_state.df_pcp = df_raw

        st.write("### ✏️ Sequenciamento Manual")
        
        dis_cols = []
        for c in st.session_state.df_pcp.columns:
            if c != "Ordem":
                dis_cols.append(c)

        df_editado = st.data_editor(st.session_state.df_pcp, disabled=dis_cols, use_container_width=True, key="editor_pcp")
        df_seq = df_editado.sort_values(by=["Ordem"]).copy()
        today = datetime.date.today()
        
        m_list = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]

        # Definição plana da agenda para evitar erros de sintaxe por quebra de linha
        agenda = {}
        agenda["Torno GL 170G - 1"] = {"data": today, "ferramental": ""}
        agenda["Torno GL 170G - 2"] = {"data": today, "ferramental": ""}
        agenda["Torno Centur - 1"] = {"data": today, "ferramental": ""}
        agenda["Torno Centur - 2"] = {"data": today, "ferramental": ""}

        maq_aloc = []
        d_ini = []
        d_fim = []
        st_ent = []
        set_reais = []
        h_tot = []
        lista_itens = df_seq.to_dict("records")

        for r in lista_itens:
            fg_str = str(r["ferramental_grupo"])
            is_gl = "8" in fg_str or "9" in fg_str
            g_maq = "Torno GL 170G" if is_gl else "Torno Centur"
            m1, m2 = f"{g_maq} - 1", f"{g_maq} - 2"

            st_m1 = max(today, agenda[m1]["data"])
            set_m1 = 0.0 if agenda[m1]["ferramental"] == fg_str else float(r["setup (min)"])
            min_m1 = set_m1 + (r["tempo unitário (min)"] * r["quantidade"])
            fim_m1 = calcular_fim_normal(st_m1, min_m1)

            st_m2 = max(today, agenda[m2]["data"])
            set_m2 = 0.0 if agenda[m2]["ferramental"] == fg_str else float(r["setup (min)"])
            min_m2 = set_m2 + (r["tempo unitário (min)"] * r["quantidade"])
            fim_m2 = calcular_fim_normal(st_m2, min_m2)

            if fim_m1 <= fim_m2:
                maq_ch, st_date, ed_date, se_at, mi_fi = m1, st_m1, fim_m1, set_m1, min_m1
            else:
                maq_ch, st_date, ed_date, se_at, mi_fi = m2, st_m2, fim_m2, set_m2, min_m2

            lim = pd.to_datetime(r["data de entrega"]).date()
            if ed_date <= lim:
                status = "✅ No Prazo"
            elif lim >= today:
                status = "⚡ No Prazo (Com Sobrecarga)"
            else:
                status = "⚠️ ATRASADO (Prazo Vencido)"

            agenda[maq_ch]["data"] = ed_date
            agenda[maq_ch]["ferramental"] = fg_str

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

        df_seq["Mês/Ano"] = pd.to_datetime(df_seq["Fim"]).dt.to_period("M").astype(str)
        df_mes = df_seq.groupby(["Mês/Ano", "Máquina"])["Total (Horas)"].sum().reset_index()
        df_mes["Horas Disponíveis"] = 157.5
        df_mes["Saldo Disponível"] = (df_mes["Horas Disponíveis"] - df_mes["Total (Horas)"]).clip(lower=0)

        st.write("## 📊 Ocupação Real")
        fig =
