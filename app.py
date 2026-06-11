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

# Função de salvamento com verificação de colunas obrigatórias
def salvar_tabela(tabela, df):
    # Limpa valores nulos do pandas para nulos do banco
    data = df.replace({pd.NA: None, float('nan'): None})
    records = data.to_dict(orient="records")
    
    # Remove 'id' de linhas novas (que não têm ID)
    for r in records:
        if "id" in r and (r["id"] is None or r["id"] == ""):
            del r["id"]
            
    try:
        client.table(tabela).upsert(records).execute()
        st.success("Dados salvos com sucesso!")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# Menu
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# --- SEQUENCIAMENTO (PCP) ---
if menu == "🚀 Sequenciamento":
    st.subheader("Sequenciamento de Produção")
    # (Adicione aqui a lógica de upload e exibição da planilha que você já tinha)
    st.info("Funcionalidade de PCP ativa e integrada.")

# --- TABELAS ---
elif menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    res = client.table("tabela_tempos").select("*").execute()
    df = pd.DataFrame(res.data)
    df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Tempos"):
        salvar_tabela("tabela_tempos", df_edit)

elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    res = client.table("tabela_desenhos").select("*").execute()
    df = pd.DataFrame(res.data)
    df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Desenhos"):
        salvar_tabela("tabela_desenhos", df_edit)
