import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Sistema Stema - Profissional", layout="wide")
st.title("🚀 Sequenciamento Profissional Stema")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=300)
def carregar_dados():
    # Carrega dados do Supabase
    tempos = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    desenhos = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
    return tempos, desenhos

df_tempos, df_desenhos = carregar_dados()

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    # 1. Preparar dados do banco para o cálculo
    # Soma os tempos de todas as ferramentas por desenho
    setup_por_desenho = df_desenhos.copy()
    # Expande a lista de ferramentas para somar os tempos corretamente
    setup_por_desenho = setup_por_desenho.assign(ferramentas=setup_por_desenho['ferramentas_necessarias'].str.split(',')).explode('ferramentas')
    setup_por_desenho['ferramentas'] = setup_por_desenho['ferramentas'].str.strip().str.lower()
    
    # Merge com tempos para pegar o valor de setup
    df_tempos['nome_ferramenta'] = df_tempos['nome_ferramenta'].str.strip().str.lower()
    setup_total = setup_por_desenho.merge(df_tempos, left_on='ferramentas', right_on='nome_ferramenta', how='left')
    setup_total = setup_total.groupby('numero_desenho')['tempo_montagem'].sum().reset_index()

    # 2. Mesclar tudo com a planilha do PCP
    df_pcp['codigo interno'] = df_pcp['codigo interno'].astype(str).str.strip()
    setup_total['numero_desenho'] = setup_total['numero_desenho'].astype(str).str.strip()
    
    df_final = df_pcp.merge(setup_total, left_on='codigo interno', right_on='numero_desenho', how='left').fillna(0)
    
    # 3. Calcular tempo final
    df_final['tempo_total_os'] = df_final['tempo_montagem'] + (pd.to_numeric(df_final['tempo unidade'], errors='coerce') * pd.to_numeric(df_final['quantidade'], errors='coerce'))
    
    # 4. Adicionar grupo de ferramentas para ordenação
    df_final = df_final.merge(df_desenhos[['numero_desenho', 'ferramentas_necessarias']], left_on='codigo interno', right_on='numero_desenho', how='left').fillna('sem_ferramenta')

    # 5. Ordenação
    df_sequenciado = df_final.sort_values(by=['ferramentas_necessarias', 'data de entrega', 'tempo_total_os'])
    
    st.success("Sequenciamento processado com motor de alta performance!")
    st.dataframe(df_sequenciado)
