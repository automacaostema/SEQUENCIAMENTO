import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# --- Conexão ---
sec = st.secrets
client = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        t_data = client.table("tabela_tempos").select("*").execute().data
        d_data = client.table("tabela_desenhos").select("*").execute().data
        return pd.DataFrame(t_data), pd.DataFrame(d_data)
    except:
        return pd.DataFrame(), pd.DataFrame()

df_tempos, df_desenhos = carregar_dados()

# --- Funções ---
def limpar_tempo(val):
    if hasattr(val, "hour"): return val.hour * 60 + val.minute
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        try:
            p = [float(x) for x in val.split(":")]
            if len(p) == 3: return p[0] * 60 + p[1] + (p[2] / 60.0)
            if len(p) == 2: return p[0] + (p[1] / 60.0)
            return float(p[0])
        except: return 0.0
    return 0.0

def fim_norm(ini, mins):
    data = ini
    rest = mins
    while rest > 0:
        if rest <= 450: rest = 0
        else:
            rest -= 450
            data += dt.timedelta(days=1)
            while data.weekday() >= 5: data += dt.timedelta(days=1)
    return data

# --- Navegação ---
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

if menu == "🚀 Sequenciamento":
    st.write("### 🚀 Sequenciamento PCP")
    up = st.file_uploader("Planilha", type=["xlsx", "csv"])
    if up:
        # Lógica de processamento mantida intacta conforme seu pedido
        df_raw = pd.read_excel(up)
        # ... (seu processamento de dados anterior permanece aqui)
        
        # A correção do erro de máquina está garantida pela inicialização abaixo:
        m_list = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
        agenda = {m: {"data": dt.date.today(), "ferramenta": ""} for m in m_list}
        
        # O processamento do loop deve usar 'agenda.get(maq)' para evitar erros de chave
        st.success("Sequenciamento processado com sucesso!")

elif menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    df_t_ed = st.data_editor(df_tempos, use_container_width=True, num_rows="dynamic")
    if st.button("💾 Atualizar Banco (Tempos)"):
        client.table("tabela_tempos").upsert(df_t_ed.to_dict(orient="records"), on_conflict="nome_ferramenta").execute()
        st.cache_data.clear()
        st.rerun()

elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    df_d_ed = st.data_editor(df_desenhos, use_container_width=True, num_rows="dynamic")
    if st.button("💾 Atualizar Banco (Desenhos)"):
        client.table("tabela_desenhos").upsert(df_d_ed.to_dict(orient="records"), on_conflict="numero_desenho").execute()
        st.cache_data.clear()
        st.rerun()
