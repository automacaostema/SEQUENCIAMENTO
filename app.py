import streamlit as st
import pandas as pd
from supabase import create_client

# 1. Configuração Inicial
st.set_page_config(page_title="Sistema Stema", layout="wide")
st.title("🚀 Sistema de Sequenciamento - Stema")

# 2. Conexão com Supabase
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erro ao conectar ao Supabase: {e}")
    st.stop()

# 3. Carregamento dos Bancos
@st.cache_data
def carregar_dados():
    tempos = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    desenhos = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
    return tempos, desenhos

df_tempos, df_desenhos = carregar_dados()

# 4. Interface de Upload
uploaded_file = st.file_uploader("Upload da Planilha PCP (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    # Ler a planilha
    df_pcp = pd.read_excel(uploaded_file)
    
    # Função principal de cálculo
    def calcular_sequenciamento(row):
        desenho_alvo = str(row['numero_desenho']).strip()
        
        # Filtra o banco de desenhos
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == desenho_alvo]
        
        if not filtro.empty:
            # Pega ferramentas e remove espaços
            ferramentas_str = str(filtro['ferramentas_necessarias'].values[0])
            ferramentas = [f.strip() for f in ferramentas_str.split(',')]
            
            # Soma os tempos de setup
            tempo_setup = df_tempos[df_tempos['nome_ferramenta'].isin(ferramentas)]['tempo_montagem'].sum()
            
            # Retorna tempo total (Setup + Produção)
            return tempo_setup + (row['tempo_unitario'] * row['quantidade'])
        return 0

    # Processar
    df_pcp['tempo_total_os'] = df_pcp.apply(calcular_sequenciamento, axis=1)
    
    # Exibir resultados
    st.subheader("Resultados do Sequenciamento")
    st.dataframe(df_pcp)
    
    # Download
    csv = df_pcp.to_csv(index=False).encode('utf-8')
    st.download_button("Baixar Sequenciamento (.csv)", csv, "sequenciamento.csv", "text/csv")
