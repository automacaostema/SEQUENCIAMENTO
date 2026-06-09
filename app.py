import streamlit as st
import pandas as pd
from supabase import create_client

# 1. Configuração da página
st.set_page_config(page_title="Sistema Stema", layout="wide")
st.title("🚀 Sistema de Sequenciamento - Stema")

# 2. Conexão
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Erro ao conectar no Supabase. Verifique suas Secrets.")
    st.stop()

# 3. Carregar dados
@st.cache_data
def carregar_bancos():
    res_tempos = supabase.table("tabela_tempos").select("*").execute()
    res_desenhos = supabase.table("tabela_desenhos").select("*").execute()
    
    df_t = pd.DataFrame(res_tempos.data)
    df_d = pd.DataFrame(res_desenhos.data)
    return df_t, df_d

df_tempos, df_desenhos = carregar_bancos()

# 4. Validação de segurança
if df_desenhos.empty:
    st.error("Sua tabela 'tabela_desenhos' está vazia no Supabase. Cadastre ao menos um desenho para começar.")
    st.stop()

# 5. Interface
uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    def calcular_sequenciamento(row):
        # Busca o desenho pelo nome da coluna que existe no seu banco
        # Se você usa 'numero_desenho' no Supabase, certifique-se que existe na planilha
        filtro = df_desenhos[df_desenhos['numero_desenho'] == str(row['numero_desenho'])]
        
        if not filtro.empty:
            ferramentas_str = str(filtro['ferramentas_necessarias'].values[0])
            ferramentas = [f.strip() for f in ferramentas_str.split(',')]
            
            tempo_setup = df_tempos[df_tempos['nome_ferramenta'].isin(ferramentas)]['tempo_montagem'].sum()
            return tempo_setup + (row['tempo_unitario'] * row['quantidade'])
        return 0

    try:
        df_pcp['tempo_total_os'] = df_pcp.apply(calcular_sequenciamento, axis=1)
        st.success("Sequenciamento processado com sucesso!")
        st.dataframe(df_pcp)
    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
        st.write("Dica: Verifique se sua planilha tem a coluna 'numero_desenho'.")
