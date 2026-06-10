import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

st.set_page_config(page_title="Sistema Stema - Profissional", layout="wide")
st.title("🚀 Sequenciamento e Otimização - Stema")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- 1. MANTENDO A BASE (Carga e Limpeza) ---
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

# --- 2. NOVA LÓGICA DE CAPACIDADE (O que estamos adicionando) ---
def calcular_maquinas(df_final):
    # Capacidade Líquida: 450 min/dia (8h45 - 1h15 almoço)
    CAP_MAQ = 450 
    
    # Exemplo de mapeamento (Se precisar mudar, me avise!)
    # Aqui estamos agrupando pelo nome da máquina que você definir no seu desenho/ferramental
    maquinas = {
        "GL170": 2, # 2 máquinas
        "Centur": 2, # 2 máquinas
        "GL250": 1  # 1 máquina
    }
    
    # Criaremos uma lógica onde o sistema aloca o tempo_total_os na máquina compatível
    # (Adicionaremos aqui o cálculo de ocupação no próximo passo)
    return df_final

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    # --- 3. MANTENDO O PROCESSAMENTO ATUAL ---
    df_pcp = pd.read_excel(uploaded_file)
    df_pcp['codigo interno'] = df_pcp['codigo interno'].astype(str).str.strip()
    df_pcp['tempo unidade'] = df_pcp['tempo unidade'].apply(limpar_tempo)
    
    # Merge com o Supabase (Profissional)
    df_final = df_pcp.merge(df_desenhos, left_on='codigo interno', right_on='numero_desenho', how='left')
    
    # Sequenciamento atual mantido
    df_sequenciado = df_final.sort_values(by=['ferramentas_necessarias', 'data de entrega'])
    
    st.success("Sequenciamento mantido e pronto para o módulo de máquinas!")
    st.dataframe(df_sequenciado)

    # --- 4. EXIBIÇÃO DO NOVO MÓDULO ---
    st.divider()
    st.subheader("📊 Gráfico de Carga das Máquinas")
    st.info("Pronto para receber a lógica de alocação por máquina.")
