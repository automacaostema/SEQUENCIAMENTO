import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

# --- Configurações Iniciais ---
st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

@st.cache_resource
def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

client = get_client()

@st.cache_data(ttl=60)
def carregar_dados():
    t_data = client.table("tabela_tempos").select("*").execute().data
    d_data = client.table("tabela_desenhos").select("*").execute().data
    return pd.DataFrame(t_data), pd.DataFrame(d_data)

# --- Funções de Apoio ---
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

# --- Menu Principal (O "if" começa aqui) ---
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

if menu == "🚀 Sequenciamento":
    st.write("### 🚀 Sequenciamento PCP")
    up = st.file_uploader("Planilha", type=["xlsx", "csv"])
    if up:
        df_raw = pd.read_excel(up)
        st.write("Planilha carregada. O sistema está pronto.")

elif menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    df_tempos, _ = carregar_dados()
    df_editado = st.data_editor(df_tempos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Tempos"):
        dados = df_editado.to_dict(orient="records")
        client.table("tabela_tempos").upsert(dados, on_conflict="nome_ferramenta").execute()
        st.cache_data.clear()
        st.rerun()

elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    _, df_desenhos = carregar_dados()
    df_editado = st.data_editor(df_desenhos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Desenhos"):
        dados = df_editado.to_dict(orient="records")
        client.table("tabela_desenhos").upsert(dados, on_conflict="numero_desenho").execute()
        st.cache_data.clear()
        st.rerun()
