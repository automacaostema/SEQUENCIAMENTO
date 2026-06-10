import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Sistema Stema - Profissional", layout="wide")
st.title("🚀 Sequenciamento e Otimização - Stema")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=300)
def carregar_dados():
    tempos = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    desenhos = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
    return tempos, desenhos

df_tempos, df_desenhos = carregar_dados()

def limpar_tempo(val):
    try:
        if isinstance(val, str) and ':' in val:
            partes = val.split(':')
            return float(partes[0]) * 60 + float(partes[1])
        return float(val)
    except:
        return 0.0

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    # Mapeamento robusto: garante que mantemos os nomes originais da sua planilha
    df_pcp.columns = [c.strip() for c in df_pcp.columns]
    
    # Conversão segura mantendo a coluna original
    df_pcp['tempo_calc'] = df_pcp['tempo unidade'].apply(limpar_tempo)
    df_pcp['qtd_calc'] = pd.to_numeric(df_pcp['quantidade'], errors='coerce').fillna(0)

    # Cálculo do setup baseado no Supabase
    def calcular_setup(cod):
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == str(cod).strip()]
        if not filtro.empty:
            ferramentas = str(filtro['ferramentas_necessarias'].values[0]).split(',')
            total = sum([df_tempos[df_tempos['nome_ferramenta'].str.lower() == f.strip().lower()]['tempo_montagem'].sum() for f in ferramentas])
            return total, str(filtro['ferramentas_necessarias'].values[0])
        return 0.0, "sem_ferramenta"

    # Aplica os cálculos sem descartar as colunas originais
    resultados = df_pcp['codigo interno'].apply(lambda x: calcular_setup(x))
    df_pcp['setup_total'], df_pcp['ferramental_grupo'] = zip(*resultados)
    
    # Cálculo final do tempo total da OS
    df_pcp['tempo_total_os'] = df_pcp['setup_total'] + (df_pcp['tempo_calc'] * df_pcp['qtd_calc'])
    
    # Ordenação profissional mantendo toda a estrutura da planilha
    df_sequenciado = df_pcp.sort_values(by=['ferramental_grupo', 'data de entrega', 'tempo_total_os'])
    
    st.success("Sequenciamento completo e colunas preservadas!")
    st.dataframe(df_sequenciado)
