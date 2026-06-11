import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# Conexão Global
sec = st.secrets
client = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])

# Funções de busca direta no banco
def fetch_table(t):
    return pd.DataFrame(client.table(t).select("*").execute().data)

# Sidebar
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# --- LÓGICA DO PCP ---
if menu == "🚀 Sequenciamento":
    st.subheader("Sequenciamento de Produção")
    up = st.file_uploader("Upload de Planilha", type=["xlsx", "csv"])
    
    if up:
        df_raw = pd.read_excel(up)
        # Processamento... (aqui entra sua lógica de cálculo)
        st.write("Planilha processada com sucesso!")
        st.dataframe(df_raw, use_container_width=True)

# --- LÓGICA DE SALVAMENTO DAS TABELAS ---
elif menu in ["🔧 Tabela Tempos", "📐 Tabela Desenhos"]:
    tabela = "tabela_tempos" if menu == "🔧 Tabela Tempos" else "tabela_desenhos"
    st.title(tabela.replace("_", " ").title())
    
    # Busca dados frescos do banco
    df = fetch_table(tabela)
    
    df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 Salvar Alterações"):
        # Limpeza para evitar erros de tipos incompatíveis
        records = df_edit.replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
        # Remove IDs nulos para novos registros criados no editor
        for r in records:
            if "id" in r and (r["id"] is None or r["id"] == ""):
                del r["id"]
        
        try:
            client.table(tabela).upsert(records).execute()
            st.success("Dados salvos no Supabase!")
            st.rerun() # Força o refresh total da página
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# Verificação de segurança
if "df_seq" in st.session_state:
    st.write("Dados ativos.")
