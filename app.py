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
    
    # Ordenação por Prazo de Entrega e Grupo para favorecer a similaridade natural na fila
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
        
        # Escolhe a máquina mais disponível cronologicamente
        maq_escolhida = m1 if agenda[m1]["data"] <= agenda[m2]["data"] else m2
        m_agenda = agenda[maq_escolhida]
        
        start_date = max(today, m_agenda["data"])
        prazo_limite = pd.to_datetime(row['data de entrega']).date()
        
        # LÓGICA DE DESCONTO DE SETUP
        ferramentas_atuais = set(f.strip().lower() for f in ferramentas_str.split(',') if f.strip() and ferramentas_str != "sem_ferramenta")
        ferramentas_anteriores = m_agenda["ferramentas"]
        
        # Apenas calcula o tempo para ferramentas que NÃO estavam na máquina
        ferramentas_novas = ferramentas_atuais - ferramentas_anteriores
        setup_min = sum([df_tempos[df_tempos['nome_ferramenta'].str.lower() == f]['tempo_montagem'].sum() for f in ferramentas_novas])
        
        # Atualiza o estado de ferramentas da máquina para o próximo lote
        m_agenda["ferramentas"] = ferramentas_atuais
        
        # Tempo Total considerando o Setup Inteligente
        tempo_total_min = setup_min + (row['tempo unitário (min)'] * row['quantidade'])
        fim_normal = calcular_fim_normal(start_date, tempo_total_min)
        
        if fim_normal <= prazo_limite:
            end_date = fim_normal
            status = "✅ No Prazo"
            m_agenda["data"] = end_date
        else:
            end_date = max(today, prazo_limite)
            status = "⚡ No Prazo (Com Sobrecarga)" if prazo_limite >= today else "⚠️ ATRASADO (Prazo Vencido)"
            m_agenda["data"] = end_date
            
        maquinas_alocadas.append(maq_escolhida)
        datas_inicio.append(start_date)
        datas_fim.append(end_date)
        status_entrega.append(status)
        setups_calculados.append(round(setup_min, 2))
        tempos_totais_horas.append(round(tempo_total_min / 60, 2))

    df_sequenciado['Máquina'] = maquinas_alocadas
    df_sequenciado['Início'] = datas_inicio
    df_sequenciado['Fim'] = datas_fim
    df_sequenciado['Status'] = status_entrega
    df_sequenciado['setup (min)'] = setups_calculados
    df_sequenciado['Total (Horas)'] = tempos_totais_horas

    # --- GRÁFICOS MENSAL ---
    df_sequenciado['Mês/Ano'] = pd.to_datetime(df_sequenciado['Fim']).dt.to_period('M').astype(str)
    df_mes = df_sequenciado.groupby(['Mês/Ano', 'Máquina'])['Total (Horas)'].sum().reset_index()
    df_mes['Horas Disponíveis'] = 157.5
    df_mes['Saldo Disponível'] = (df_mes['Horas Disponíveis'] - df_mes['Total (Horas)']).clip(lower=0)

    st.write("## 📊 Ocupação Real Mensal por Máquina (Com Desconto de Setup)")
    fig = px.bar(df_mes, x='Mês/Ano', y=['Total (Horas)', 'Saldo Disponível'], 
                 facet_col='Máquina', facet_col_wrap=2, title="Distribuição de Horas Otimizada",
                 labels={'value': 'Horas', 'variable': 'Status'}, barmode='stack')
    st.plotly_chart(fig, use_container_width=True)

    # --- SEPARAÇÃO POR ABAS ---
    st.divider()
    st.write("## 🗓️ Filas de Trabalho Individuais por Máquina")
    
    lista_maquinas = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
    abas = st.tabs(lista_maquinas)
    
    for i, maq in enumerate(lista_maquinas):
        with abas[i]:
            df_maq = df_sequenciado[df_sequenciado['Máquina'] == maq].drop(columns=['Máquina', 'tempo total (min)', 'Mês/Ano'])
            cols = ['Status', 'Início', 'Fim', 'data de entrega', 'Total (Horas)', 'setup (min)'] + [c for c in df_maq.columns if c not in ['Status', 'Início', 'Fim', 'data de entrega', 'Total (Horas)', 'setup (min)']]
            st.dataframe(df_maq[cols], use_container_width=True)
