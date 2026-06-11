import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# Conexão
sec = st.secrets
client = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])

# Funções auxiliares
def limpar_tempo(val):
    if hasattr(val, "hour"): return val.hour * 60 + val.minute
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        try:
            p = [float(x) for x in val.split(":")]
            if len(p) == 3: return p[0]*60 + p[1] + (p[2]/60.0)
            if len(p) == 2: return p[0] + (p[1]/60.0)
            return float(p[0])
        except: return 0.0
    return 0.0

def fim_norm(ini, mins):
    data = ini
    while mins > 0:
        if mins <= 450: mins = 0
        else:
            mins -= 450
            data += dt.timedelta(days=1)
            while data.weekday() >= 5: data += dt.timedelta(days=1)
    return data

# Navegação
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# --- LÓGICA DE SALVAMENTO ---
def salvar_banco(tabela, df):
    # Remove NaN e trata IDs
    df_clean = df.replace({pd.NA: None, float('nan'): None})
    records = df_clean.to_dict(orient="records")
    for r in records:
        if "id" in r and (r["id"] is None or pd.isna(r["id"])):
            del r["id"]
    try:
        client.table(tabela).upsert(records).execute()
        st.success("Salvo com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# --- SEQUENCIAMENTO ---
if menu == "🚀 Sequenciamento":
    st.write("### ✏️ Sequenciamento")
    up = st.file_uploader("Upload", type=["xlsx", "csv"])
    
    # Carrega dados do banco
    t_data = client.table("tabela_tempos").select("*").execute().data
    d_data = client.table("tabela_desenhos").select("*").execute().data
    df_tempos = pd.DataFrame(t_data)
    df_desenhos = pd.DataFrame(d_data)

    if up:
        df_raw = pd.read_excel(up)
        # Processamento (mantenha sua lógica original aqui)
        st.write("Processamento concluído.")
        st.dataframe(df_raw)

# --- TABELAS ---
elif menu in ["🔧 Tabela Tempos", "📐 Tabela Desenhos"]:
    tabela = "tabela_tempos" if menu == "🔧 Tabela Tempos" else "tabela_desenhos"
    st.title(tabela.replace("_", " ").title())
    
    res = client.table(tabela).select("*").execute()
    df = pd.DataFrame(res.data)
    
    df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar"):
        salvar_banco(tabela, df_edit)
