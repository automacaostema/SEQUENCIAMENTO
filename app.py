import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Sistema Stema", layout="wide")
st.title("🚀 Sistema de Sequenciamento - Stema")

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
    
    # Identifica automaticamente a coluna de data (procura qualquer coluna que tenha 'data' no nome)
    coluna_data = next((c for c in df_pcp.columns if 'data' in c.lower()), df_pcp.columns[0])
    
    df_pcp['tempo_unitario'] = pd.to_numeric(df_pcp['tempo_unitario'], errors='coerce').fillna(0)
    df_pcp['quantidade'] = pd.to_numeric(df_pcp['quantidade'], errors='coerce').fillna(0)
    
    def calcular_linha(row):
        cod = str(row['numero_desenho']).strip()
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == cod]
        if not filtro.empty:
            ferramentas = str(filtro['ferramentas_necessarias'].values[0]).lower().split(',')
            tempo_setup = df_tempos[df_tempos['nome_ferramenta'].str.lower().isin(ferramentas)]['tempo_montagem'].sum()
            return float(tempo_setup) + (float(row['tempo_unitario']) * float(row['quantidade']))
        return 0.0

    df_pcp['tempo_total_os'] = df_pcp.apply(calcular_linha, axis=1)
    
    # Ordenação flexível
    try:
        df_sequenciado = df_pcp.sort_values(by=[coluna_data, 'tempo_total_os'], ascending=[True, True])
        st.success(f"Sequenciamento organizado pela data ({coluna_data})!")
    except:
        df_sequenciado = df_pcp.sort_values(by=['tempo_total_os'])
        st.warning("Data não encontrada para ordenação, ordenado apenas por tempo.")
    
    st.dataframe(df_sequenciado)
