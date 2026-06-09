import streamlit as st
import pandas as pd
from supabase import create_client

# Configuração da página
st.set_page_config(page_title="Gestão de Produção", layout="wide")
st.title("Sequenciamento de Produção - Stema Usinagem")

# Inicializar conexão com Supabase usando as Secrets
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# Função para buscar dados do banco
def get_data(table):
    response = supabase.table(table).select("*").execute()
    return pd.DataFrame(response.data)

# Carregar tabelas de referência
try:
    df_tempos = get_data("tabela_tempos") # Ajuste o nome da tabela conforme seu Supabase
    df_desenhos = get_data("tabela_desenhos")
except Exception as e:
    st.error(f"Erro ao conectar com Supabase: {e}")

# Interface de Upload
uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    # Lógica de cálculo (simulada com os dados do Supabase)
    def calcular_carga(row):
        # Aqui o sistema buscará as ferramentas no df_desenhos e o tempo no df_tempos
        # Exemplo simplificado de busca:
        return 15 # Placeholder para o tempo calculado
    
    df_pcp['tempo_total'] = df_pcp.apply(calcular_carga, axis=1)
    
    st.subheader("Resultado do Sequenciamento")
    st.dataframe(df_pcp)
    st.success("Cálculo concluído!")
