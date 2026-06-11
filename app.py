import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# --- CONFIGURAÇÃO ---
sec = st.secrets
url = sec["SUPABASE_URL"]
key = sec["SUPABASE_KEY"]
client = create_client(url, key)

# --- FUNÇÕES ---
@st.cache_data(ttl=60) # TTL reduzido para forçar refresh
def buscar_dados_banco(tabela):
    return client.table(tabela).select("*").execute().data

def limpar_tempo(val):
    if hasattr(val, "hour"): return val.hour * 60 + val.minute
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        try:
            p = [float(x) for x in val.split(":")]
            if len(p) == 3: return p[0] * 60 + p[1] + (p[2] / 60.0)
            if len(p) == 2: return p[0] + (p[1] / 60.0)
            if len(p) == 1: return p[0]
        except: return 0.0
    return 0.0

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# --- ABAS DE CONFIGURAÇÃO ---
if menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    data = buscar_dados_banco("tabela_tempos")
    df = pd.DataFrame(data)
    df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 Salvar Tempos"):
        # Limpeza para evitar erros de JSON
        records = df_edit.replace({pd.NA: None}).to_dict(orient="records")
        # Remove IDs nulos para novos registros
        for r in records:
            if r.get("id") is None: del r["id"]
        
        client.table("tabela_tempos").upsert(records).execute()
        st.cache_data.clear() # Limpa o cache para recarregar dados novos
        st.success("Dados salvos!")
        st.rerun()

elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    data = buscar_dados_banco("tabela_desenhos")
    df = pd.DataFrame(data)
    df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 Salvar Desenhos"):
        records = df_edit.replace({pd.NA: None}).to_dict(orient="records")
        for r in records:
            if r.get("id") is None: del r["id"]
            
        client.table("tabela_desenhos").upsert(records).execute()
        st.cache_data.clear()
        st.success("Dados salvos!")
        st.rerun()

# --- SEQUENCIAMENTO (Lógica mantida similar à anterior) ---
elif menu == "🚀 Sequenciamento":
    st.title("🚀 Sequenciamento")
    # Nota: carregar_dados aqui deve usar a função buscar_dados_banco definida acima
    # ... (seu código de processamento de planilha aqui) ...
