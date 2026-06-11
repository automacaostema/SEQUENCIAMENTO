import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# Conexão
sec = st.secrets
client = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])

menu = st.sidebar.radio("Navegação", ["🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# Função de salvamento forçado
def salvar_tabela(tabela, df):
    # Converte tudo para formato que o Supabase aceita
    # Remove colunas que podem ser autoincrementadas se estiverem vazias
    data = df.replace({pd.NA: None, float('nan'): None})
    records = data.to_dict(orient="records")
    
    # Remove 'id' se for None, para permitir criação de novos itens
    for r in records:
        if "id" in r and r["id"] is None:
            del r["id"]
            
    client.table(tabela).upsert(records).execute()
    st.cache_data.clear()
    st.rerun()

if menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    res = client.table("tabela_tempos").select("*").execute()
    df = pd.DataFrame(res.data)
    
    df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 Salvar no Banco"):
        salvar_tabela("tabela_tempos", df_edit)

elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    res = client.table("tabela_desenhos").select("*").execute()
    df = pd.DataFrame(res.data)
    
    df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 Salvar no Banco"):
        salvar_tabela("tabela_desenhos", df_edit)
