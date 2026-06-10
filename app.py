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
    
    # Ordenação por semana e similaridade de ferramenta
    df_pcp['semana_entrega'] = pd.to_datetime(df_pcp['data de entrega']).dt.isocalendar().week
    df_sequenciado = df_pcp.sort_values(by=['semana_entrega', 'ferramental_grupo', 'data de entrega']).copy()

    # --- MOTOR DE ALOCAÇÃO INTELIGENTE (PREFERÊNCIA POR FERRAMENTAL) ---
    today = datetime.date.today()
    agenda = {
        "Torno GL 170G - 1": {"data": today, "ferramental": ""},
        "Torno GL 170G - 2": {"data": today, "ferramental": ""},
        "Torno Centur - 1": {"data": today, "ferramental": ""},
        "Torno Centur - 2": {"data": today, "ferramental": ""}
    }

    maquinas_alocadas = []
    datas_inicio = []
    datas_fim = []
    status_entrega = []
    setups_reais = []
    horas_totais = []

    for idx, row in df_sequenciado.iterrows():
        grupo_maq = "Torno GL 170G" if ("Ø8" in str(row['ferramental_grupo']) or "Ø9" in str(row['ferramental_grupo'])) else "Torno Centur"
        m1, m2 = f"{grupo_maq} - 1", f"{grupo_maq} - 2"
        
        # Se uma das duas máquinas já está com essa ferramenta instalada, manda para ela e ZERA o setup
        if agenda[m1]["ferramental"] == str(row['ferramental_grupo']) and agenda[m1]["ferramental"] != "sem_ferramenta":
            maq_escolhida = m1
            setup_atual = 0.0
        elif agenda[m2]["ferramental"] == str(row['ferramental_grupo']) and agenda[m2]["ferramental"] != "sem_ferramenta":
            maq_escolhida = m2
            setup_atual = 0.0
        else:
            # Se nenhuma tem a ferramenta pronta, escolhe a que terminar mais cedo
            maq_escolhida = m1 if agenda[m1]["data"] <= agenda[m2]["data"] else m2
            setup_atual = float(row['setup (min)'])
            
        start_date = max(today, agenda[maq_escolhida]["data"])
        prazo_limite = pd.to_datetime(row['data de entrega']).date()
        
        # Recalcula o tempo dinamicamente descontando o setup se reaproveitado
        minutos = setup_atual + (row['tempo unitário (min)'] * row['quantidade'])
        fim_normal = calcular_fim_normal(start_date, minutos)
        
        if fim_normal <= prazo_limite:
            end_date = fim_normal
            status = "✅ No Prazo"
            agenda[maq_escolhida]["data"] = end_date
        else:
            end_date = max(today, prazo_limite)
            status = "⚡ No Prazo (Com Sobrecarga)" if prazo_limite >= today else "⚠️ ATRASADO (Prazo Vencido)"
            agenda[maq_escolhida]["data"] = end_date
            
        agenda[maq_escolhida]["ferramental"] = str(row['ferramental_grupo'])
        
        maquinas_alocadas.append(maq_escolhida)
        datas_inicio.append(start_date)
        datas_fim.append(end_date)
        status_entrega.append(status)
        setups_reais.append(setup_atual)
        horas_totais.append(round(minutos / 60, 2))

    df_sequenciado['Máquina'] = maquinas_alocadas
    df_sequenciado['Início'] = datas_inicio
    df_sequenciado['Fim'] = datas_fim
    df_sequenciado['Status'] = status_entrega
    df_sequenciado['setup (min)'] = setups_reais
    df_sequenciado['Total (Horas)'] = horas_totais

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
