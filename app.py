import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime

st.set_page_config(page_title="Sistema Stema - PCP", layout="wide")
st.title("🚀 Sequenciamento Otimizado (Sem Atraso Cascata) - Stema")

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
    
    # --- ORDENAÇÃO POR SEMANA E FERRAMENTA ---
    df_pcp['semana_entrega'] = pd.to_datetime(df_pcp['data de entrega']).dt.isocalendar().week
    df_sequenciado = df_pcp.sort_values(by=['semana_entrega', 'ferramental_grupo', 'data de entrega']).copy()

    # --- MOTOR DE ALOCAÇÃO INDIVIDUAL E SOBRECARGA ---
    today = datetime.date.today()
    agenda = {
        "Torno GL 170G - 1": today, "Torno GL 170G - 2": today,
        "Torno Centur - 1": today, "Torno Centur - 2": today
    }

    maquinas_alocadas = []
    datas_inicio = []
    datas_fim = []
    status_entrega = []

    for idx, row in df_sequenciado.iterrows():
        grupo_maq = "Torno GL 170G" if ("Ø8" in str(row['ferramental_grupo']) or "Ø9" in str(row['ferramental_grupo'])) else "Torno Centur"
        m1, m2 = f"{grupo_maq} - 1", f"{grupo_maq} - 2"
        
        # Escolhe a máquina com maior disponibilidade atual
        maq_escolhida = m1 if agenda[m1] <= agenda[m2] else m2
        start_date = max(today, agenda[maq_escolhida])
        
        prazo_limite = pd.to_datetime(row['data de entrega']).date()
        minutos = row['tempo total (min)']
        
        fim_normal = calcular_fim_normal(start_date, minutos)
        
        if fim_normal <= prazo_limite:
            end_date = fim_normal
            status = "✅ No Prazo"
            agenda[maq_escolhida] = end_date
        else:
            # Força a entrega absorvendo a sobrecarga para não atrasar os próximos
            end_date = max(today, prazo_limite)
            status = "⚡ No Prazo (Com Sobrecarga)" if prazo_limite >= today else "⚠️ ATRASADO (Prazo Vencido)"
            agenda[maq_escolhida] = end_date
            
        maquinas_alocadas.append(maq_escolhida)
        datas_inicio.append(start_date)
        datas_fim.append(end_date)
        status_entrega.append(status)

    df_sequenciado['Máquina'] = maquinas_alocadas
    df_sequenciado['Início'] = datas_inicio
    df_sequenciado['Fim'] = datas_fim
    df_sequenciado['Status'] = status_entrega
    df_sequenciado['Total (Horas)'] = (df_sequenciado['tempo total (min)'] / 60).round(2)

    # --- GRÁFICO MENSAL RECALCULADO ---
    df_sequenciado['Mês/Ano'] = pd.to_datetime(df_sequenciado['Fim']).dt.to_period('M').astype(str)
    df_mes = df_sequenciado.groupby(['Mês/Ano', 'Máquina'])['Total (Horas)'].sum().reset_index()
    df_mes['Horas Disponíveis'] = 157.5
    df_mes['Saldo Disponível'] = (df_mes['Horas Disponíveis'] - df_mes['Total (Horas)']).clip(lower=0)

    st.write("## 📊 Ocupação Real Mensal por Máquina")
    fig = px.bar(df_mes, x='Mês/Ano', y=['Total (Horas)', 'Saldo Disponível'], 
                 facet_col='Máquina', facet_col_wrap=2, title="Distribuição de Horas",
                 labels={'value': 'Horas', 'variable': 'Status'}, barmode='stack')
    st.plotly_chart(fig, use_container_width=True)

    # --- SEPARAÇÃO POR ABAS DE MÁQUINAS ---
    st.divider()
    st.write("## 🗓️ Filas de Trabalho Individuais por Máquina")
    
    lista_maquinas = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
    abas = st.tabs(lista_maquinas)
    
    for i, maq in enumerate(lista_maquinas):
        with abas[i]:
            df_maq = df_sequenciado[df_sequenciado['Máquina'] == maq].drop(columns=['Máquina', 'tempo total (min)', 'Mês/Ano', 'semana_entrega'])
            cols = ['Status', 'Início', 'Fim', 'data de entrega', 'Total (Horas)', 'setup (min)'] + [c for c in df_maq.columns if c not in ['Status', 'Início', 'Fim', 'data de entrega', 'Total (Horas)', 'setup (min)']]
            st.dataframe(df_maq[cols], use_container_width=True)
