import datetime as dt
import pandas as pd
import streamlit as st
from supabase import create_client

# Configuração da página
st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# --- Conexão Supabase ---
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

# --- Funções de Cálculo ---
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

# --- Menu Principal ---
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# --- Aba 1: Sequenciamento ---
if menu == "🚀 Sequenciamento":
    st.write("### 🚀 Sequenciamento PCP")
    up = st.file_uploader("Upload da Planilha", type=["xlsx", "csv"])
    if up:
        df_tempos, df_desenhos = carregar_dados()
        df = pd.read_excel(up)
        df.columns = [c.strip() for c in df.columns]
        
        # Processamento básico
        df["tempo unitário (min)"] = df["tempo unidade"].apply(limpar_tempo)
        df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0)
        
        st.write("Dados processados. Visualize abaixo:")
        st.dataframe(df, use_container_width=True)

# --- Aba 2: Tabela Tempos ---
elif menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    df_tempos, _ = carregar_dados()
    df_editado = st.data_editor(df_tempos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Tempos"):
        client.table("tabela_tempos").upsert(df_editado.to_dict(orient="records"), on_conflict="nome_ferramenta").execute()
        st.cache_data.clear()
        st.success("Tempos salvos no Supabase!")
        st.rerun()

# --- Aba 3: Tabela Desenhos ---
elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    _, df_desenhos = carregar_dados()
    df_editado = st.data_editor(df_desenhos, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Desenhos"):
        client.table("tabela_desenhos").upsert(df_editado.to_dict(orient="records"), on_conflict="numero_desenho").execute()
        st.cache_data.clear()
        st.success("Desenhos salvos no Supabase!")
        st.rerun()
