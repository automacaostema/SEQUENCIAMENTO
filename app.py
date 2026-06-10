import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px

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
    
    # Garantir limpeza das colunas da planilha
    df_pcp['codigo interno'] = df_pcp['codigo interno'].astype(str).str.strip()
    df_pcp['tempo unidade'] = df_pcp['tempo unidade'].apply(limpar_tempo)
    df_pcp['quantidade'] = pd.to_numeric(df_pcp['quantidade'], errors='coerce').fillna(0)

    # Preparar banco para merge
    setup_por_desenho = df_desenhos.copy()
    setup_por_desenho['ferramentas_lista'] = setup_por_desenho['ferramentas_necessarias'].str.split(',')
    
    # Calcular tempo de setup total por desenho
    def somar_setup(lista_ferramentas):
        if not isinstance(lista_ferramentas, list): return 0
        total = 0
        for f in lista_ferramentas:
            nome = f.strip().lower()
            tempo = df_tempos[df_tempos['nome_ferramenta'].str.lower() == nome]['tempo_montagem'].sum()
            total += tempo
        return total

    df_desenhos['tempo_setup_total'] = setup_por_desenho['ferramentas_lista'].apply(somar_setup)

    # Merge final mantendo todas as colunas originais
    df_final = df_pcp.merge(df_desenhos, left_on='codigo interno', right_on='numero_desenho', how='left')
    
    # Calcular tempo total (Setup + Tempo Unidade * Quantidade)
    df_final['tempo_total_os'] = df_final['tempo_setup_total'] + (df_final['tempo unidade'] * df_final['quantidade'])
    
    # Ordenação
    df_sequenciado = df_final.sort_values(by
