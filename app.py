import streamlit as st
import pandas as pd
from supabase import create_client

# Configuração da página
st.set_page_config(page_title="Sistema Stema", layout="wide")
st.title("🚀 Sistema de Sequenciamento - Stema")

# Conexão
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# Função para carregar dados
@st.cache_data(ttl=60) # Atualiza a cada 60 segundos
def carregar_bancos():
    df_t = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    df_d = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
    return df_t, df_d

df_tempos, df_desenhos = carregar_bancos()

# Upload da planilha
uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    def calcular_sequenciamento(row):
        # Converte para string e remove espaços
        desenho_alvo = str(row['numero_desenho']).strip()
        
        # Filtra no banco de desenhos
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == desenho_alvo]
        
        if not filtro.empty:
            ferramentas_str = str(filtro['ferramentas_necessarias'].values[0])
            ferramentas = [f.strip().lower() for f in ferramentas_str.split(',')]
            
            # Soma tempos (ajustado para ser case-insensitive)
            # Garantindo que as ferramentas sejam comparadas sem diferenciar maiúsculas/minúsculas
            df_tempos['nome_ferramenta_lower'] = df_tempos['nome_ferramenta'].str.lower()
            tempo_setup = df_tempos[df_tempos['nome_ferramenta_lower'].isin(ferramentas)]['tempo_montagem'].sum()
            
            return tempo_setup + (row['tempo_unitario'] * row['quantidade'])
        return 0

    # Processamento
    try:
        df_pcp['tempo_total_os'] = df_pcp.apply(calcular_sequenciamento, axis=1)
        st.success("Sequenciamento processado com sucesso!")
        st.dataframe(df_pcp)
    except Exception as e:
        st.error(f"Erro no processamento: {e}")
