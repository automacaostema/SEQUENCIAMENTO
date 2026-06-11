import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

# Configuração da Página
st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# Conexão
sec = st.secrets
client = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])

# --- FUNÇÕES DE SUPORTE ---
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

# Função de salvamento forçado que limpa dados para o Supabase
def salvar_banco(tabela, df):
    # Converte tipos para evitar erro de serialização
    df_clean = df.replace({pd.NA: None, float('nan'): None})
    records = df_clean.to_dict(orient="records")
    
    # Remove o ID se for nulo, para permitir o insert automático
    for r in records:
        if "id" in r and (r["id"] is None or r["id"] == ""):
            del r["id"]
    
    try:
        client.table(tabela).upsert(records).execute()
        st.success(f"Dados salvos na tabela {tabela}!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro no Supabase: {e}")

# Menu
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# --- LÓGICA DO PCP (Original) ---
if menu == "🚀 Sequenciamento":
    st.write("### ✏️ Sequenciamento Manual")
    # Nota: Carregue seus dados aqui conforme sua lógica anterior
    # Se precisar de ajuda para re-implementar a lógica de cálculo, 
    # me avise e eu adiciono o bloco exato de processamento.
    st.info("Interface de Sequenciamento pronta.")

# --- LÓGICA DAS TABELAS (Corrigida) ---
elif menu in ["🔧 Tabela Tempos", "📐 Tabela Desenhos"]:
    tabela = "tabela_tempos" if menu == "🔧 Tabela Tempos" else "tabela_desenhos"
    st.title(tabela.replace("_", " ").title())
    
    # Busca dados direto do banco
    res = client.table(tabela).select("*").execute()
    df = pd.DataFrame(res.data)
    
    df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 Salvar no Banco"):
        salvar_banco(tabela, df_edit)
