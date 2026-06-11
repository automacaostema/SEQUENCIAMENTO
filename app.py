import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

# --- CONFIGURAÇÃO ---
st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

sec = st.secrets
client = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])

# --- MENU ---
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# --- FUNÇÕES DE SUPORTE ---
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

def salvar_banco(tabela, df):
    # Limpa dados para o formato do Supabase
    data = df.replace({pd.NA: None, float('nan'): None})
    records = data.to_dict(orient="records")
    for r in records:
        if "id" in r and (r["id"] is None or pd.isna(r["id"])):
            del r["id"]
    try:
        client.table(tabela).upsert(records).execute()
        st.success("Salvou!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro no banco: {e}")

# --- INTERFACES ---
if menu == "🚀 Sequenciamento":
    st.write("### ✏️ Sequenciamento")
    up = st.file_uploader("Upload Planilha", type=["xlsx", "csv"])
    if up:
        df_raw = pd.read_excel(up)
        # (Sua lógica de cálculo viria aqui)
        st.write("Planilha carregada.")
        st.dataframe(df_raw)

elif menu in ["🔧 Tabela Tempos", "📐 Tabela Desenhos"]:
    tabela = "tabela_tempos" if menu == "🔧 Tabela Tempos" else "tabela_desenhos"
    st.title(tabela.replace("_", " ").title())
    
    # Busca dados atuais
    res = client.table(tabela).select("*").execute()
    df = pd.DataFrame(res.data)
    
    df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Alterações"):
        salvar_banco(tabela, df_edit)
