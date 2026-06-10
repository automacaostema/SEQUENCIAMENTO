import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime

st.set_page_config(page_title="Sistema Stema - PCP", layout="wide")
st.title("🚀 Sequenciamento Cronológico por Prazo - Stema")

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
    
    # Definição automática temporária de máquina
    df_pcp['maquina'] = df_pcp.apply(lambda r: "Torno GL 170G" if ("Ø8" in str(r['ferramental_grupo']) or "Ø9" in str(r['ferramental_grupo'])) else "Torno Centur", axis=1)
    
    # CORREÇÃO DA ORDENAÇÃO: Prazo de Entrega vem PRIMEIRO que a similaridade
    df_sequenciado = df_pcp.sort_values(by=['maquina', 'data de entrega', 'ferramental_grupo', 'tempo total (min)']).copy()

    # --- SIMULAÇÃO DA CRONOLOGIA ---
    def proximo_dia_util(data):
        data += datetime.timedelta(days=1)
        while data.weekday() >= 5:
            data += datetime.timedelta(days=1)
        return data

    minutos_disponiveis_dia = 900 
    agenda_maquinas = {
        "Torno GL 170G": {"data_atual": datetime.date.today(), "minutos_usados": 0},
        "Torno Centur": {"data_atual": datetime.date.today(), "minutos_usados": 0}
    }

    datas_inicio = []
    datas_fim = []

    for idx, row in df_sequenciado.iterrows():
        maq = row['maquina']
        tempo_restante = row['tempo total (min)']
        agenda = agenda_maquinas[maq]
        
        datas_inicio.append(agenda["data_atual"])
        
        while tempo_restante > 0:
            minutos_livres_hoje = minutos_disponiveis_dia - agenda["minutos_usados"]
            if tempo_restante <= minutos_livres_hoje:
                agenda["minutos_usados"] += tempo_restante
                tempo_restante = 0
            else:
                tempo_restante -= minutos_livres_hoje
                agenda["data_atual"] = proximo_dia_util(agenda["data_atual"])
                agenda["minutos_usados"] = 0
                
        datas_fim.append(agenda["data_atual"])
        if agenda["minutos_usados"] == minutos_disponiveis_dia:
            agenda["data_atual"] = proximo_dia_util(agenda["data_atual"])
            agenda["minutos_usados"] = 0

    df_sequenciado['Início Fabricação'] = datas_inicio
    df_sequenciado['Fim Fabricação'] = datas_fim
    df_sequenciado['tempo total (horas)'] = (df_sequenciado['tempo total (min)'] / 60).round(2)

    # Identificação de prazos estourados
    def checar_status(row):
        prazo_limite = pd.to_datetime(row['data de entrega']).date()
        return "✅ No Prazo" if row['Fim Fabricação'] <= prazo_limite else "⚠️ ATRASADO"

    df_sequenciado['Status Entrega'] = df_sequenciado.apply(checar_status, axis=1)

    # --- GRÁFICO MENSAL ---
    df_sequenciado['Mês/Ano'] = pd.to_datetime(df_sequenciado['Fim Fabricação']).dt.to_period('M').astype(str)
    df_mes = df_sequenciado.groupby(['Mês/Ano', 'maquina'])['tempo total (horas)'].sum().reset_index()
    df_mes['Horas Disponíveis'] = 315.0
    df_mes['Saldo Disponível'] = (df_mes['Horas Disponíveis'] - df_mes['tempo total (horas)']).clip(lower=0)

    st.write("## 📊 Carga de Máquina Mensal (Horas)")
    fig = px.bar(df_mes, x='Mês/Ano', y=['tempo total (horas)', 'Saldo Disponível'], 
                 facet_col='maquina', title="Horas Ocupadas vs Disponíveis por Mês",
                 labels={'value': 'Horas', 'variable': 'Status'}, barmode='stack')
    st.plotly_chart(fig, use_container_width=True)

    # --- EXIBIÇÃO DA FILA REORGANIZADA ---
    st.divider()
    st.write("## 🗓️ Sequência de Fabricação Ajustada por Prazo")
    for maq in ["Torno GL 170G", "Torno Centur"]:
        st.subheader(f"📋 Fila Cronológica: {maq}")
        df_exibir = df_sequenciado[df_sequenciado['maquina'] == maq].drop(columns=['maquina', 'tempo total (min)', 'Mês/Ano'])
        
        # Reposiciona as colunas de data para o começo da visualização
        cols = ['Status Entrega', 'Início Fabricação', 'Fim Fabricação', 'data de entrega'] + [c for c in df_exibir.columns if c not in ['Status Entrega', 'Início Fabricação', 'Fim Fabricação', 'data de entrega']]
        st.dataframe(df_exibir[cols], use_container_width=True)
