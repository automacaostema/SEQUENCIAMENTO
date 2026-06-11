import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# Conexão
@st.cache_resource
def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

client = get_client()

@st.cache_data(ttl=10)
def carregar_dados():
    try:
        t_data = client.table("tabela_tempos").select("*").execute().data
        d_data = client.table("tabela_desenhos").select("*").execute().data
        return pd.DataFrame(t_data), pd.DataFrame(d_data)
    except Exception as e:
        st.error(f"Erro ao ler banco: {e}")
        return pd.DataFrame(), pd.DataFrame()

menu = st.sidebar.radio("Navegação", ["🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# Função de salvamento genérica com tratamento de erro
def salvar_no_banco(tabela, df, chave):
    try:
        dados = df.to_dict(orient="records")
        # O upsert aqui tentará salvar tudo
        client.table(tabela).upsert(dados, on_conflict=chave).execute()
        st.success(f"Tabela {tabela} salva com sucesso!")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        st.json(df.to_dict(orient="records")) # Exibe os dados para conferência

if menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    df_t, _ = carregar_dados()
    df_edit = st.data_editor(df_t, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Tempos"):
        salvar_no_banco("tabela_tempos", df_edit, "nome_ferramenta")

elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    _, df_d = carregar_dados()
    df_edit = st.data_editor(df_d, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Desenhos"):
        salvar_no_banco("tabela_desenhos", df_edit, "numero_desenho")
