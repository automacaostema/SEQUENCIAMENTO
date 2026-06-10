import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime

st.set_page_config(page_title="Sistema Stema - PCP", layout="wide")
st.title("🚀 Sequenciamento por Prazo e Carga de Máquinas - Stema")

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
    df_pcp['tempo total (min)'] = df_pcp['setup (min)'] + (df_pcp['tempo unitário (min)'] * df_pcp['quantidade'])
    
    # ORDENAÇÃO SOLICITADA: Data de entrega em 1º lugar, Similaridade em 2º lugar
    df_sequenciado = df_pcp.sort_values(by=['data de entrega', 'ferramental_grupo', 'tempo total (min)']).copy()

    # --- SIMULAÇÃO COM 4 MÁQUINAS INDIVIDUAIS ---
    def proximo_dia_util(data):
        data += datetime.timedelta(days=1)
        while data.weekday() >= 5:
            data += datetime.timedelta(days=1)
        return data

    MINUTOS_DIARIOS_POR_MAQUINA = 450 # 7h30min livres
    
    # Agenda separada para cada uma das 4 máquinas
    agenda = {
        "Torno GL 170G - 1": {"data": datetime.date.today(), "min": 0},
        "Torno GL 170G - 2": {"data": datetime.date.today(), "min": 0},
        "Torno Centur - 1": {"data": datetime.date.today(), "min": 0},
        "Torno Centur - 2": {"data": datetime.date.today(), "min": 0}
    }

    maquinas_alocadas = []
    datas_inicio = []
    datas_fim = []

    for idx, row in df_sequenciado.iterrows():
        # Identifica o tipo de torno necessário
        grupo_maq = "Torno GL 170G" if ("Ø8" in str(row['ferramental_grupo']) or "Ø9" in str(row['ferramental_grupo'])) else "Torno Centur"
        m1 = f"{grupo_maq} - 1"
        m2 = f"{grupo_maq} - 2"
        
        # Escolhe a máquina que estiver livre mais cedo (Balanceamento de Carga)
        score1 = (agenda[m1]["data"], agenda[m1]["min"])
        score2 = (agenda[m2]["data"], agenda[m2]["min"])
        
        maq_escolhida = m1 if score1 <= score2 else m2
        m_agenda = agenda[maq_escolhida]
        
        maquinas_alocadas.append(maq_escolhida)
        datas_inicio.append(m_agenda["data"])
        
        tempo_restante = row['tempo total (min)']
        while tempo_restante > 0:
            livre_hoje = MINUTOS_DIARIOS_POR_MAQUINA - m_agenda["min"]
            if tempo_restante <= livre_hoje:
                m_agenda["min"] += tempo_restante
                tempo_restante = 0
            else:
                tempo_restante -= livre_hoje
                m_agenda["data"] = proximo_dia_util(m_agenda["data"])
                m_agenda["min"] = 0
                
        datas_fim.append(m_agenda["data"])
        if m_agenda["min"] == MINUTOS_DIARIOS_POR_MAQUINA:
            m_agenda["data"] = proximo_dia_util(m_agenda["data"])
            m_agenda["min"] = 0

    df_sequenciado['Máquina Alocada'] = maquinas_alocadas
    df_sequenciado['Início Fabricação'] = datas_inicio
    df_sequenciado['Fim Fabricação'] = datas_fim
    df_sequenciado['tempo total (horas)'] = (df_sequenciado['tempo total (min)'] / 60).round(2)

    def checar_status(row):
        prazo_limite = pd.to_datetime(row['data de entrega']).date()
        return "✅ No Prazo" if row['Fim Fabricação'] <= prazo_limite else "⚠️ ATRASADO"

    df_sequenciado['Status Entrega'] = df_sequenciado.apply(checar_status, axis=1)

    # --- GRÁFICO MENSAL INDIVIDUALIZADO POR MÁQUINA ---
    df_sequenciado['Mês/Ano'] = pd.to_datetime(df_sequenciado['Fim Fabricação']).dt.to_period('M').astype(str)
    df_mes = df_sequenciado.groupby(['Mês/Ano', 'Máquina Alocada'])['tempo total (horas)'].sum().reset_index()
    
    # 21 dias úteis x 7.5 horas = 157.5 horas disponíveis por máquina no mês
    df_mes['Horas Disponíveis'] = 157.5
    df_mes['Saldo Disponível'] = (df_mes['Horas Disponíveis'] - df_mes['tempo total (horas)']).clip(lower=0)

    st.write("## 📊 Capacidade Disponível vs Ocupada por Mês (Por Máquina)")
    fig = px.bar(df_mes, x='Mês/Ano', y=['tempo total (horas)', 'Saldo Disponível'], 
                 facet_col='Máquina Alocada', facet_col_wrap=2, title="Distribuição Mensal de Carga de Trabalho",
                 labels={'value': 'Horas', 'variable': 'Status'}, barmode='stack')
    st.plotly_chart(fig, use_container_width=True)

    # --- EXIBIÇÃO DA FILA GERAL SEQUENCIADA ---
    st.divider()
    st.write("## 🗓️ Fila Única de Fabricação (Ordenada por Urgência e Semelhança)")
    
    df_exibir = df_sequenciado.drop(columns=['tempo total (min)', 'Mês/Ano'])
    cols_ordenadas = ['Status Entrega', 'Máquina Alocada', 'Início Fabricação', 'Fim Fabricação', 'data de entrega'] + [c for c in df_exibir.columns if c not in ['Status Entrega', 'Máquina Alocada', 'Início Fabricação', 'Fim Fabricação', 'data de entrega']]
    
    st.dataframe(df_exibir[cols_ordenadas], use_container_width=True)
