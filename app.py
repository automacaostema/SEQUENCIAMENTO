import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="PCP", layout="wide")
st.title("🚀 Sequenciamento Otimizado")

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

up = st.file_uploader("Planilha", type=["xlsx", "csv"])

if up:
    # Trava de segurança adicionada aqui para evitar o AttributeError
    if "df_pcp" not in st.session_state or "f_name" not in st.session_state or st.session_state.f_name != up.name:
        st.session_state.f_name = up.name
        df_raw = pd.read_excel(up)
@@ -84,76 +83,82 @@
    st.info("Altere os números da coluna 'Ordem' para recalcular automaticamente.")

    dis_cols = [c for c in st.session_state.df_pcp.columns if c != "Ordem"]
    df_editado = st.data_editor(st.session_state.df_pcp, disabled=dis_cols, use_container_width=True)
    st.session_state.df_pcp = df_editado
    
    # Fixado com chave nativa para evitar bugs de atualização
    df_editado = st.data_editor(
        st.session_state.df_pcp, 
        disabled=dis_cols, 
        use_container_width=True, 
        key="editor_pcp"
    )

    df_seq = df_editado.sort_values(by=["Ordem"]).copy()
    today = datetime.date.today()
    m_list = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]

    agenda = {n: {"data": today, "ferramental": ""} for n in m_list}
    maquinas_alocadas, datas_inicio, datas_fim, status_entrega, setups_reais, horas_totais = [], [], [], [], [], []
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
        status = "✅ No Prazo" if ed_date <= lim else ("⚡ No Prazo (Com Sobrecarga)" if lim >= today else "⚠️ ATRASADO (Prazo Vencido)")

        agenda[maq_ch]["data"] = ed_date
        agenda[maq_ch]["ferramental"] = fg_str

        maquinas_alocadas.append(maq_ch)
        datas_inicio.append(st_date)
        datas_fim.append(ed_date)
        status_entrega.append(status)
        setups_reais.append(se_at)
        horas_totais.append(round(mi_fi / 60, 2))

    df_seq["Máquina"] = maquinas_alocadas
    df_seq["Início"] = datas_inicio
    df_seq["Fim"] = datas_fim
    df_seq["Status"] = status_entrega
    df_seq["setup (min)"] = setups_reais
    df_seq["Total (Horas)"] = horas_totais

    # --- GRÁFICOS ---
    df_seq["Mês/Ano"] = pd.to_datetime(df_seq["Fim"]).dt.to_period("M").astype(str)
    df_mes = df_seq.groupby(["Mês/Ano", "Máquina"])["Total (Horas)"].sum().reset_index()
    df_mes["Horas Disponíveis"] = 157.5
    df_mes["Saldo Disponível"] = (df_mes["Horas Disponíveis"] - df_mes["Total (Horas)"]).clip(lower=0)

    st.write("## 📊 Ocupação Real")
    fig = px.bar(df_mes, x="Mês/Ano", y=["Total (Horas)", "Saldo Disponível"], facet_col="Máquina", facet_col_wrap=2, title="Horas", labels={"value": "Horas", "variable": "Status"}, barmode="stack")
    st.plotly_chart(fig, use_container_width=True)

    # --- ABAS ---
    st.divider()
    st.write("## 🗓️ Filas de Trabalho")
    abas = st.tabs(m_list)

    for i, maq in enumerate(m_list):
        with abas[i]:
            df_m = df_seq[df_seq["Máquina"] == maq].drop(columns=["Máquina", "Mês/Ano"])
            f_cols = ["Status", "Início", "Fim", "data de entrega", "Total (Horas)", "setup (min)"]
            cols = f_cols + [c for c in df_m.columns if c not in f_cols]
            st.dataframe(df_m[cols], use_container_width=True)
