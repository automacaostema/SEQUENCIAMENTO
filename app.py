import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Sistema Stema", layout="wide")
st.title("🚀 Otimizador de Setup - Stema")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=60)
def carregar_dados():
    tempos = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    desenhos = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
    return tempos, desenhos

df_tempos, df_desenhos = carregar_dados()

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    # Identifica colunas automaticamente
    col_data = next((c for c in df_pcp.columns if 'data' in c.lower()), df_pcp.columns[-1])
    df_pcp['data_limite'] = pd.to_datetime(df_pcp[col_data])
    
    def buscar_ferramental(cod):
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == str(cod).strip()]
        return str(filtro['ferramentas_necessarias'].values[0]) if not filtro.empty else "sem_ferramenta"

    # Criar grupo de ferramentas
    df_pcp['ferramental_grupo'] = df_pcp['numero_desenho'].apply(buscar_ferramental)
    
    # ALGORITMO DE OTIMIZAÇÃO:
    # 1. Agrupa pelo grupo de ferramentas para manter o setup igual por mais tempo
    # 2. Dentro do grupo, ordena pela data de entrega mais próxima (para não atrasar)
    df_sequenciado = df_pcp.sort_values(
        by=['ferramental_grupo', 'data_limite'], 
        ascending=[True, True]
    )
    
    st.success("Sequenciamento otimizado para Setup (Ferramentas Agrupadas)!")
    st.dataframe(df_sequenciado)
    
    # Resumo para o operador
    st.subheader("Resumo por Setup")
    resumo = df_sequenciado.groupby('ferramental_grupo').agg({
        'numero_desenho': 'count',
        'data_limite': 'min'
    }).rename(columns={'numero_desenho': 'Total de OS'})
    st.table(resumo)
