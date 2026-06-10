import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime

st.set_page_config(page_title="Sistema Stema - PCP", layout="wide")
st.title("🚀 Sequenciamento com Setup Inteligente - Stema")

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
            elif len(parts) == 1: return parts[0]
        except: return 0.0
    return 0.0

def calcular_fim_normal(data_inicio, minutos_totais):
    data = data_inicio
    tempo_restante = minutos_totais
    while tempo_restante > 0:
        if tempo_restante <= 450:
            tempo_restante = 0
        else:
            tempo_restante -= 450
            data += datetime.timedelta(days=1)
            while data.weekday() >= 5:
                data += datetime.timedelta(days=1)
    return data

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df_pcp = pd.read_excel(uploaded_file)
    df_pcp.columns = [c.strip() for c in df_pcp.columns]
    
    df_pcp['tempo unitário (min)'] = df_pcp['tempo unidade'].apply(limpar_tempo)
    df_pcp['quantidade'] = pd.to_numeric(df_pcp['quantidade'], errors='coerce').fillna(0)

    def obter_grupo_ferramentas(cod):
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == str(cod).strip()]
        return str(filtro['ferramentas_necessarias'].values[0]) if not filtro.empty else "sem_ferramenta"

    df_pcp['ferramental_grupo'] = df_pcp['codigo interno'].apply(obter_grupo_ferramentas)
    
    # Ordenação por Prazo de Entrega e Grupo
    df_sequenciado = df_pcp.sort_values(by=['data de entrega', 'ferramental_grupo']).copy()

    # --- MOTOR DE ALOCAÇÃO COM SETUP REUTILIZÁVEL ---
    today = datetime.date.today()
    agenda = {
        "Torno GL 170G - 1": {"data": today, "ferramentas": set()},
        "Torno GL 170G - 2": {"data": today, "ferramentas": set()},
        "Torno Centur - 1": {"data": today, "ferramentas": set()},
        "Torno Centur - 2": {"data": today, "ferramentas": set()}
    }

    maquinas_alocadas = []
    datas_inicio = []
    datas_fim = []
    status_entrega = []
    setups_calculados = []
    tempos_totais_horas = []

    for idx, row in df_sequenciado.iterrows():
        ferramentas_str = str(row['ferramental_grupo'])
        grupo_maq = "Torno GL 170G" if ("Ø8" in ferramentas_str or "Ø9" in ferramentas_str) else "Torno Centur"
        m1, m2 = f"{grupo_maq} - 1", f"{grupo_maq} - 2"
        
        # Escolhe
