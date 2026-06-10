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
    df_pcp.columns = [c.strip() for c in df_pcp.columns]
    
    # Cálculos internos
    df_pcp['tempo_calc'] = df_pcp['tempo unidade'].apply(limpar_tempo)
    df_pcp['qtd_calc'] = pd.to_numeric(df_pcp['quantidade'], errors='coerce').fillna(0)

    # Cálculo Setup
    def calcular_setup(cod):
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == str(cod).strip()]
        if not filtro.empty:
            ferramentas = str(filtro['ferramentas_necessarias'].values[0]).split(',')
            total = sum([df_tempos[df_tempos['nome_ferramenta'].str.lower() == f.strip().lower()]['tempo_montagem'].sum() for f in ferramentas])
            return total, str(filtro['ferramentas_necessarias'].values[0])
        return 0.0, "sem_ferramenta"

    resultados = df_pcp['codigo interno'].apply(lambda x: calcular_setup(x))
    df_pcp['setup_minutos'], df_pcp['ferramental_grupo'] = zip(*resultados)
    
    # Cálculo Final: (Setup + (Tempo Unitário * Quantidade)) / 60 para virar HORAS
    df_pcp['tempo_total_horas'] = (df_pcp['setup_minutos'] + (df_pcp['tempo_calc'] * df_pcp['qtd_calc'])) / 60
    
    # Arredondamento para visualização limpa
    df_pcp['tempo_total_horas'] = df_pcp['tempo_total_horas'].round(2)
    
    # Ordenação
    df_sequenciado = df_pcp.sort_values(by=['ferramental_grupo', 'data de entrega', 'tempo_total_horas'])
    
    # Limpeza da exibição
    df_exibicao = df_sequenciado.drop(columns=['tempo_calc', 'qtd_calc', 'setup_minutos'])
    
    st.success("Tabela com Tempo Total em HORAS disponível:")
    st.dataframe(df_exibicao)
