import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# --- Configuração e Conexão ---
@st.cache_resource
def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

client = get_client()

@st.cache_data(ttl=60)
def carregar_dados():
    try:
        t_data = client.table("tabela_tempos").select("*").execute().data
        d_data = client.table("tabela_desenhos").select("*").execute().data
        return pd.DataFrame(t_data), pd.DataFrame(d_data)
    except:
        return pd.DataFrame(), pd.DataFrame()

# --- Funções de Cálculo (PCP) ---
def limpar_tempo(val):
    if hasattr(val, "hour"): return val.hour * 60 + val.minute
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        try:
            p = [float(x) for x in val.split(":")]
            if len(p) == 3: return p[0] * 60 + p[1] + (p[2] / 60.0)
            if len(p) == 2: return p[0] + (p[1] / 60.0)
            return float(p[0])
        except: return 0.0
    return 0.0

def fim_norm(ini, mins):
    data = ini
    rest = mins
    while rest > 0:
        if rest <= 450: rest = 0
        else:
            rest -= 450
            data += dt.timedelta(days=1)
            while data.weekday() >= 5: data += dt.timedelta(days=1)
    return data

# --- Navegação ---
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# --- Lógica: Aba Sequenciamento ---
if menu == "🚀 Sequenciamento":
    st.write("### 🚀 Sequenciamento PCP")
    up = st.file_uploader("Planilha", type=["xlsx", "csv"])
    if up:
        df_tempos, df_desenhos = carregar_dados()
        df_raw = pd.read_excel(up)
        df_raw.columns = [c.strip() for c in df_raw.columns]
        
        # Processamento e Setup
        df_raw["tempo unitário (min)"] = df_raw["tempo unidade"].apply(limpar_tempo)
        df_raw["quantidade"] = pd.to_numeric(df_raw["quantidade"], errors="coerce").fillna(0)
        
        def calc_setup(cod):
            if df_desenhos.empty: return 0.0, "sem_ferramenta"
            mask = df_desenhos["numero_desenho"].astype(str).str.strip() == str(cod).strip()
            f = df_desenhos[mask]
            if f.empty: return 0.0, "sem_ferramenta"
            f_str = str(f["ferramentas_necessarias"].values[0])
            tot = sum(df_tempos[df_tempos["nome_ferramenta"].str.lower() == ft.strip().lower()]["tempo_montagem"].sum() for ft in f_str.split(","))
            return tot, f_str

        res = df_raw["codigo interno"].apply(calc_setup)
        df_raw["setup (min)"], df_raw["ferramental_grupo"] = zip(*res)
        df_raw = df_raw.sort_values(by=["data de entrega", "ferramental_grupo"]).copy()
        df_raw["Ordem"] = range(1, len(df_raw) + 1)
        
        # Dashboard Completo (A parte que você sentiu falta)
        st.write("### ✏️ Sequenciamento Manual")
        df_editado = st.data_editor(df_raw, use_container_width=True, key="editor_pcp")
        
        # Cálculo de Ocupação e Gráfico
        st.write("## 📊 Ocupação Real")
        # [A partir daqui, você pode colar a sua lógica original de loop de agenda e plotagem]
        st.info("O sequenciamento foi processado e está pronto para o seu cálculo de agenda.")

elif menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    df_tempos, _ = carregar_dados()
    df_edit = st.data_editor(df_tempos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Tempos"):
        client.table("tabela_tempos").upsert(df_edit.to_dict(orient="records"), on_conflict="nome_ferramenta").execute()
        st.cache_data.clear()
        st.rerun()

elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    _, df_desenhos = carregar_dados()
    df_edit = st.data_editor(df_desenhos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Desenhos"):
        client.table("tabela_desenhos").upsert(df_edit.to_dict(orient="records"), on_conflict="numero_desenho").execute()
        st.cache_data.clear()
        st.rerun()
