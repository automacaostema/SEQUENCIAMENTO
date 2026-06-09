import streamlit as st
import pandas as pd
from supabase import create_client

# Conexão
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("Sequenciamento Stema")

# Carrega bancos
try:
    # Ajuste: garantindo que pegamos os dados corretamente
    response_tempos = supabase.table("tabela_tempos").select("*").execute()
    df_tempos = pd.DataFrame(response_tempos.data)
    
    response_desenhos = supabase.table("tabela_desenhos").select("*").execute()
    df_desenhos = pd.DataFrame(response_desenhos.data)
except Exception as e:
    st.error(f"Erro ao carregar do Supabase: {e}")
    st.stop()

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    
    def calcular_total(row):
        # BUSCA usando o nome exato do banco: numero_desenho
        # Se na planilha do Excel a coluna se chamar 'desenho', usamos row['desenho']
        filtro = df_desenhos[df_desenhos['numero_desenho'] == row['desenho']]
        
        if not filtro.empty:
            ferramentas_str = filtro['ferramentas_necessarias'].values[0]
            ferramentas = [f.strip() for f in str(ferramentas_str).split(',')]
            
            # Soma tempos das ferramentas encontradas
            tempo_setup = df_tempos[df_tempos['nome_ferramenta'].isin(ferramentas)]['tempo_montagem'].sum()
            
            return tempo_setup + (row['tempo_unitario'] * row['quantidade'])
        return 0

    try:
        df_pcp['tempo_total_os'] = df_pcp.apply(calcular_total, axis=1)
        st.success("Sequenciamento concluído!")
        st.dataframe(df_pcp)
    except Exception as e:
        st.error(f"Erro no processamento da linha: {e}")
        st.write("Colunas detectadas na planilha:", df_pcp.columns.tolist())
