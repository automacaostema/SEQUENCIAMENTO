import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Sistema Stema", layout="wide")
st.title("🚀 Sistema de Sequenciamento - Stema")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=60)
def carregar_bancos():
    df_t = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    df_d = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
    return df_t, df_d

df_tempos, df_desenhos = carregar_bancos()

def converter_tempo(val):
    try:
        # Se for tempo (time/datetime), extrai minutos
        if isinstance(val, (pd.Timestamp, pd.Timedelta)):
            return float(val.hour * 60 + val.minute)
        return float(val)
    except:
        return 0.0

uploaded_file = st.file_uploader("Suba a planilha do PCP (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        df_pcp = pd.read_excel(uploaded_file)
        
        # DEBUG: Mostrar o que está sendo lido
        st.write("--- DEBUG: Verificação ---")
        st.write("Colunas na planilha:", df_pcp.columns.tolist())
        st.write("Valores originais de 'tempo_unitario':", df_pcp['tempo_unitario'].head().tolist())
        
        # Conversão
        df_pcp['tempo_unitario_convertido'] = df_pcp['tempo_unitario'].apply(converter_tempo)
        st.write("Valores convertidos:", df_pcp['tempo_unitario_convertido'].head().tolist())
        
        def calcular_sequenciamento(row):
            desenho_alvo = str(row['numero_desenho']).strip()
            filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == desenho_alvo]
            
            if not filtro.empty:
                ferramentas_str = str(filtro['ferramentas_necessarias'].values[0])
                ferramentas = [f.strip().lower() for f in ferramentas_str.split(',')]
                df_tempos_clean = df_tempos.copy()
                df_tempos_clean['nome_ferramenta_lower'] = df_tempos_clean['nome_ferramenta'].str.lower()
                tempo_setup = df_tempos_clean[df_tempos_clean['nome_ferramenta_lower'].isin(ferramentas)]['tempo_montagem'].sum()
                
                return float(tempo_setup) + (float(row['tempo_unitario_convertido']) * float(row['quantidade']))
            return 0

        df_pcp['tempo_total_os'] = df_pcp.apply(calcular_sequenciamento, axis=1)
        st.success("Sequenciamento processado!")
        st.dataframe(df_pcp)
        
    except Exception as e:
        st.error(f"Erro crítico: {e}")
