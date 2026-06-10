import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import datetime

st.set_page_config(layout="wide")
st.title("🚀 Sequenciamento PCP - Completo")

# 1. Conexão
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    t_df = pd.DataFrame(supabase.table("tabela_tempos").select("*").execute().data)
    d_df = pd.DataFrame(supabase.table("tabela_desenhos").select("*").execute().data)
except Exception as e:
    st.error(f"Erro Conexão: {e}")
    st.stop()

# 2. Funções Auxiliares
def para_minutos(val):
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, datetime.time): return val.hour * 60 + val.minute
    if isinstance(val, str):
        try:
            p = [int(x) for x in val.split(':')]
            return p[0]*60 + p[1]
        except: return 0.0
    return 0.0

def calcular_fim(inicio, mins):
    data = inicio
    restante = mins
    while restante > 0:
        if restante <= 450: restante = 0
        else:
            restante -= 450
            data += datetime.timedelta(days=1)
            while data.weekday() >= 5: data += datetime.timedelta(days=1)
    return data

# 3. Processamento
uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [c.strip() for c in df.columns]
    
    def get_f(cod):
        f = d_df[d_df['numero_desenho'].astype(str).str.strip() == str(cod).strip()]
        return str(f['ferramentas_necessarias'].values[0]) if not f.empty else "sem"
    
    df['ferramental_grupo'] = df['codigo interno'].apply(get_f)
    df = df.sort_values(by=['data de entrega', 'ferramental_grupo'])
    
    m_names = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
    agenda = {n: {"data": datetime.date.today(), "ferramentas": set()} for n in m_names}
    
    res = []
    for i in range(len(df)):
        r = df.iloc[i]
        f_s = str(r['ferramental_grupo'])
        g = "Torno GL 170G" if ("Ø8" in f_s or "Ø9" in f_s) else "Torno Centur"
        maq = f"{g} - 1" if agenda[f"{g} - 1"]["data"] <= agenda[f"{g} - 2"]["data"] else f"{g} - 2"
        
        # Lógica de Setup Inteligente
        f_atuais = set(f.strip().lower() for f in f_s.split(',') if f.strip() and f_s != "sem")
        f_novas = f_atuais - agenda[maq]["ferramentas"]
        setup = sum([t_df[t_df['nome_ferramenta'].str.lower()==f]['tempo_montagem'].sum() for f in f_novas]) if f_novas else 0
        
        t_unit = para_minutos(r['tempo unidade'])
        total_m = setup + (t_unit * float(r['quantidade']))
        
        fim = calcular_fim(agenda[maq]["data"], total_m)
        agenda[maq].update({"data": fim, "ferramentas": f_atuais})
        
        res.append({
            "Máquina": maq, "Início": agenda[maq]["data"], "Fim": fim, 
            "Status": "✅ No Prazo" if fim <= pd.to_datetime(r['data de entrega']).date() else "⚠️ ATRASADO",
            "Total (Horas)": round(total_m/60, 2), "setup (min)": setup, **r
        })
    
    df_final = pd.DataFrame(res)
    
    # 4. Gráfico
    st.write("## 📊 Ocupação Real")
    df_mes = df_final.groupby(['Máquina', 'Status'])['Total (Horas)'].sum().reset_index()
    fig = px.bar(df_mes, x='Máquina', y='Total (Horas)', color='Status', barmode='group')
    st.plotly_chart(fig, use_container_width=True)
    
    # 5. Abas
    abas = st.tabs(m_names)
    for i, maq in enumerate(m_names):
        with abas[i]:
            st.dataframe(df_final[df_final["Máquina"] == maq], use_container_width=True)
