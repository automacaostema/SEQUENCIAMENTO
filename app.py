import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px

st.set_page_config(page_title="Sistema Stema - PCP", layout="wide")
st.title("🚀 Sequenciamento e Ocupação de Máquinas - Stema")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=300)
def carregar_dados():
    tempos = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    desenhos = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
    return tempos, desenhos

df_tempos, df_desenhos = carregar_dados()

def limpar_tempo(val):
    if hasattr(val, 'hour') and hasattr(val, 'minute') and hasattr(val, 'second'):
        return val.hour * 60 + val.minute + (val.second / 60.0)
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        try:
            parts = [float(x) for x in val.split(':')]
            if len(parts) == 3: return parts[0] * 60 + parts[1] + (parts[2] / 60.0)
            elif len(parts) == 2: return parts[0] + (parts[1] / 60.0)
        except: return 0.0
    return 0.0

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    df_pcp.columns = [c.strip() for c in df_pcp.columns]
    
    df_pcp['tempo unitário (min)'] = df_pcp['tempo unidade'].apply(limpar_tempo)
    df_pcp['quantidade'] = pd.to_numeric(df_pcp['quantidade'], errors='coerce').fillna(0)

    def calcular_setup(cod):
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == str(cod).strip()]
        if not filtro.empty:
            ferramentas = str(filtro['ferramentas_necessarias'].values[0]).split(',')
            total = sum([df_tempos[df_tempos['nome_ferramenta'].str.lower() == f.strip().lower()]['tempo_montagem'].sum() for f in ferramentas])
            return total, str(filtro['ferramentas_necessarias'].values[0])
        return 0.0, "sem_ferramenta"

    resultados = df_pcp['codigo interno'].apply(lambda x: calcular_setup(x))
    df_pcp['setup (min)'], df_pcp['ferramental_grupo'] = zip(*resultados)
    
    # Tempo Total em Horas
    df_pcp['tempo total (horas)'] = ((df_pcp['setup (min)'] + (df_pcp['tempo unitário (min)'] * df_pcp['quantidade'])) / 60).round(2)
    df_pcp['tempo unitário (min)'] = df_pcp['tempo unitário (min)'].round(2)
    
    # --- REGRA DE DESTINAÇÃO DE MÁQUINAS ---
    def definir_maquina(row):
        grupo = str(row['ferramental_grupo'])
        if "Ø8" in grupo or "Ø9" in grupo:
            return "Torno GL 170G"
        return "Torno Centur"
        
    df_pcp['maquina'] = df_pcp.apply(definir_maquina, axis=1)
    
    # Ordenação Estratégica: Ferramenta (Similaridade) -> Prazo -> Tempo
    df_sequenciado = df_pcp.sort_values(by=['maquina', 'ferramental_grupo', 'data de entrega', 'tempo total (horas)'])

    # --- GRÁFICOS DE DISPOSIÇÃO DE HORAS ---
    # 2 máquinas de cada = 15 horas disponíveis por grupo (7.5h x 2)
    HORAS_DISPONIVEIS_GRUPO = 15.0 
    
    st.write("## 📊 Ocupação das Máquinas (Carga Total)")
    col1, col2 = st.columns(2)
    
    for i, maq in enumerate(["Torno GL 170G", "Torno Centur"]):
        df_maq = df_sequenciado[df_sequenciado['maquina'] == maq]
        horas_ocupadas = df_maq['tempo total (horas)'].sum()
        
        dados_grafico = pd.DataFrame({
            'Status': ['Horas Ocupadas', 'Horas Disponíveis'],
            'Horas': [horas_ocupadas, max(0.0, HORAS_DISPONIVEIS_GRUPO - horas_ocupadas)]
        })
        
        fig = px.pie(dados_grafico, values='Horas', names='Status', 
                     title=f"{maq} (Capacidade do Grupo: {HORAS_DISPONIVEIS_GRUPO}h)",
                     color_discrete_sequence=['#EF553B', '#636EFA'])
        
        if i == 0: col1.plotly_chart(fig, use_container_width=True)
        else: col2.plotly_chart(fig, use_container_width=True)

    # --- LISTAS DE SEQUENCIAMENTO DE FABRICAÇÃO ---
    st.divider()
    st.write("## 🗓️ Sequência de Fabricação por Máquina")
    
    for maq in ["Torno GL 170G", "Torno Centur"]:
        st.subheader(f"📋 Fila de Produção: {maq}")
        df_fila = df_sequenciado[df_sequenciado['maquina'] == maq].drop(columns=['maquina'])
        st.dataframe(df_fila, use_container_width=True)
