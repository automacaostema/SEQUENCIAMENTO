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
    # Função corrigida para tratar HH:MM:SS ou MM:SS
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        try:
            parts = [float(x) for x in val.split(':')]
            if len(parts) == 3: # HH:MM:SS
                return parts[0] * 60 + parts[1] + parts[2] / 60
            elif len(parts) == 2: # MM:SS
                return parts[0] + parts[1] / 60
            elif len(parts) == 1:
                return parts[0]
        except:
            return 0.0
    return 0.0

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    df_pcp.columns = [c.strip() for c in df_pcp.columns]
    
    # 1. Tempo Unitário (Convertido para Minutos)
    df_pcp['tempo unitário (min)'] = df_pcp['tempo unidade'].apply(limpar_tempo)
    df_pcp['quantidade'] = pd.to_numeric(df_pcp['quantidade'], errors='coerce').fillna(0)

    # 2. Setup (Cálculo do banco)
    def calcular_setup(cod):
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == str(cod).strip()]
        if not filtro.empty:
            ferramentas = str(filtro['ferramentas_necessarias'].values[0]).split(',')
            total = sum([df_tempos[df_tempos['nome_ferramenta'].str.lower() == f.strip().lower()]['tempo_montagem'].sum() for f in ferramentas])
            return total, str(filtro['ferramentas_necessarias'].values[0])
        return 0.0, "sem_ferramenta"

    resultados = df_pcp['codigo interno'].apply(lambda x: calcular_setup(x))
    df_pcp['setup (min)'], df_pcp['ferramental_grupo'] = zip(*resultados)
    
    # 3. Tempo Total (Setup + (Unitário * Quantidade))
    # Mantendo em minutos para precisão e exibindo resultado final
    df_pcp['tempo total (min)'] = df_pcp['setup (min)'] + (df_pcp['tempo unitário (min)'] * df_pcp['quantidade'])
    
    # Ordenação
    df_sequenciado = df_pcp.sort_values(by=['ferramental_grupo', 'data de entrega', 'tempo total (min)'])
    
    st.success("Tabela processada com cálculo de tempo corrigido!")
    st.dataframe(df_sequenciado)
