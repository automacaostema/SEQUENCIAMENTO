import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime

st.set_page_config(page_title="Sistema Stema - PCP", layout="wide")
st.title("🚀 Sequenciamento Otimizado - Stema")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


@st.cache_data(ttl=300)
def carregar_dados():
    t_data = supabase.table("tabela_tempos").select("*").execute().data
    d_data = supabase.table("tabela_desenhos").select("*").execute().data
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


uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    df_pcp.columns = [c.strip() for c in df_pcp.columns]

    df_pcp["tempo unitário (min)"] = df_pcp["tempo unidade"].apply(limpar_tempo)
    df_pcp["quantidade"] = pd.to_numeric(
        df_pcp["quantidade"], errors="coerce"
    ).fillna(0)

    def calcular_setup(cod):
        cod_str = str(cod).strip()
        d_df = df_desenhos
        mask_des = d_df["numero_desenho"].astype(str).str.strip() == cod_str
        filtro = d_df[mask_des]
        if not filtro.empty:
            ferr_str = str(filtro["ferramentas_necessarias"].values[0])
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
    df_pcp["setup (min)"], df_pcp["ferramental_grupo"] = zip(*resultados)

    df_sequenciado = df_pcp.sort_values(
        by=["data de entrega", "ferramental_grupo"]
    ).copy()

    today = datetime.date.today()
    agenda = {
        "Torno GL 170G - 1": {"data": today, "ferramental": ""},
        "Torno GL 170G - 2": {"data": today, "ferramental": ""},
        "Torno Centur - 1": {"data": today, "ferramental": ""},
        "Torno Centur - 2": {"data": today, "ferramental": ""},
    }

    maquinas_alocadas = []
    datas_inicio = []
    datas_fim = []
    status_entrega = []
    setups_reais = []
    horas_totais = []

    for idx, row in df_sequenciado.iterrows():
        fg_str = str(row["ferramental_grupo"])
        is_gl = "Ø8" in fg_str or "Ø9" in fg_str
        grupo_maq = "Torno GL 170G" if is_gl else "Torno Centur"
        m1, m2 = f"{grupo_maq} - 1", f"{grupo_maq} - 2"

        start_m1 = max(today, agenda[m1]["data"])
        is_same_m1 = agenda[m1]["ferramental"] == fg_str
        setup_m1 = 0.0 if is_same_m1 else float(row["setup (min)"])
        minutos_m1 = setup_m1 + (
            row["tempo unitário (min)"] * row["quantidade"]
        )
        fim_m1 = calcular_fim_normal(start_m1, minutos_m1)

        start_m2 = max(today, agenda[m2]["data"])
        is_same_m2 = agenda[m2]["ferramental"] == fg_str
        setup_m2 = 0.0 if is_same_m2 else float(row["setup (min)"])
        minutos_m2 = setup_m2 + (
            row["tempo unitário (min)"] * row["quantidade"]
        )
        fim_m2 = calcular_fim_normal(start_m2, minutos_m2)

        if fim_m1 <= fim_m2:
            maq_escolhida = m1
            start_date = start_m1
            end_date = fim_m1
            setup_atual = setup_m1
            minutos_finais = minutos_m1
        else:
            maq_escolhida = m2
            start_date = start_m2
            end_date = fim_m2
            setup_atual = setup_m2
            minutos_finais = minutos_m2

        prazo_limite = pd.to_datetime(row["data de entrega"]).date()

        if end_date <= prazo_limite:
            status = "✅ No Prazo"
        else:
            is_futuro = prazo_limite >= today
            status = (
                "⚡ No Prazo (Com Sobrecarga)"
                if is_futuro
                else "⚠️ ATRASADO (Prazo Vencido)"
            )

        agenda[maq_escolhida]["data"] = end_date
        agenda[maq_escolhida]["ferramental"] = fg_str

        maquinas_alocadas.append(maq_escolhida)
        datas_inicio.append(start_date)
        datas_fim.append(end_date)
        status_entrega.append(status)
        setups_reais.append(setup_atual)
        horas_totais.append(round(minutos_finais / 60, 2))

    df_sequenciado["Máquina"] = maquinas_alocadas
    df_sequenciado["Início"] = datas_inicio
    df_sequenciado["Fim"] = datas_fim
    df_sequenciado["Status"] = status_entrega
    df_sequenciado["setup (min)"] = setups_reais
    df_sequenciado["Total (Horas)"] = horas_totais

    df_sequenciado["Mês/Ano"] = (
        pd.to_datetime(df_sequenciado["Fim"]).dt.to_period("M").astype(str)
    )
    grp = df_sequenciado.groupby(["Mês/Ano", "Máquina"])
    df_mes = grp["Total (Horas)"].sum().reset_index()
    df_mes["Horas Disponíveis"] = 157.5
    df_mes["Saldo Disponível"] = (
        df_mes["Horas Disponíveis"] - df_mes["Total (Horas)"]
    ).clip(lower=0)

    st.write("## 📊 Ocupação Real Mensal por Máquina")
    fig = px.bar(
        df_mes,
        x="Mês/Ano",
        y=["Total (Horas)", "Saldo Disponível"],
        facet_col="Máquina",
        facet_col_wrap=2,
        title="Distribuição de Horas",
        labels={"value": "Horas", "variable": "Status"},
        barmode="stack",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.write("## 🗓️ Filas de Trabalho Individuais por Máquina")

    lista_maquinas = [
        "Torno GL 170G - 1",
        "Torno GL 170G - 2",
        "Torno Centur - 1",
        "Torno Centur - 2",
    ]
    abas = st.tabs(lista_maquinas)

    for i, maq in enumerate(lista_maquinas):
        with abas[i]:
            mask_m = df_sequenciado["Máquina"] == maq
            df_maq = df_sequenciado[mask_m].drop(columns=["Máquina", "Mês/Ano"])
            fix_cols = [
                "Status",
                "Início",
                "Fim",
                "data de entrega",
                "Total (Horas)",
                "setup (min)",
            ]
            other_cols = [c for c in df_maq.columns if c not in fix_cols]
            cols = fix_cols + other_cols
            st.dataframe(df_maq[cols], use_container_width=True)
