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
    if "f_name" not in st.session_state or st.session_state.f_name != up.name:
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
    st.info("Altere os números da coluna 'Ordem' para recalcular.")
    
    dis_cols = [c for c in st.session_state.df_pcp.columns if c != "Ordem"]
    df_editado = st.data_editor(st.session_state.df_pcp, disabled=dis_cols, use_container_width=True)
    st.session_state.df_pcp = df_editado

    df_seq = df_editado.sort_values(by=["Ordem"]).copy()
    today = datetime.date.today()
    m_list = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]

    agenda = {n: {"data": today, "ferramental": ""} for n in m_list}

    maquinas_alocadas, datas_inicio, datas_fim, status_entrega, setups_reais, horas_totais = [], [], [], [], [], []

    for idx, row in df_seq.iterrows():
        fg_str = str(row
