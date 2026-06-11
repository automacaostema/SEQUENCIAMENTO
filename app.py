import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# --- Conexão Supabase ---
@st.cache_resource
def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

client = get_client()

@st.cache_data(ttl=60)
def carregar_dados():
    try:
        t_data = client.table("tabela_tempos").select("*").execute().data
        d_data = client.table("tabela_desenhos").select("*").execute().data
        return pd.DataFrame(t_data), pd.DataFrame(d_data)
    except:
        return pd.DataFrame(), pd.DataFrame()

# --- Funções do PCP ---
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
        df_tempos, df_desenhos = carregar_dados()
        df_raw = pd.read_excel(up)
        df_raw.columns = [c.strip() for c in df_raw.columns]
        
        # Cálculos iniciais
        df_raw["tempo unitário (min)"] = df_raw["tempo unidade"].apply(limpar_tempo)
        df_raw["quantidade"] = pd.to_numeric(df_raw["quantidade"], errors="coerce").fillna(0)
        
        def calc_setup(cod):
            if df_desenhos.empty: return 0.0, "sem_ferramenta"
            mask = df_desenhos["numero_desenho"].astype(str).str.strip() == str(cod).strip()
            f = df_desenhos[mask]
            if f.empty: return 0.0, "sem_ferramenta"
            f_str = str(f["ferramentas_necessarias"].values[0])
            tot = sum(df_tempos[df_tempos["nome_ferramenta"].str.lower() == ft.strip().lower()]["tempo_montagem"].sum() for ft in f_str.split(","))
            return tot, f_str

        res = df_raw["codigo interno"].apply(calc_setup)
        df_raw["setup (min)"], df_raw["ferramental_grupo"] = zip(*res)
        df_raw = df_raw.sort_values(by=["data de entrega", "ferramental_grupo"]).copy()
        df_raw["Ordem"] = range(1, len(df_raw) + 1)
        
        df_editado = st.data_editor(df_raw, use_container_width=True)
        
        # --- Lógica de Fila Automática Original ---
        today = dt.date.today()
        m_list = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
        agenda = {m: {"data": today, "ferramental": ""} for m in m_list}
        maq_aloc, d_ini, d_fim, st_ent, set_reais, h_tot = [], [], [], [], [], []
        
        for r in df_editado.to_dict("records"):
            fg = str(r["ferramental_grupo"])
            is_gl = "8" in fg or "9" in fg
            g_maq = "Torno GL 170G" if is_gl else "Torno Centur"
            m1, m2 = f"{g_maq} - 1", f"{g_maq} - 2"
            
            # Cálculo de datas e status
            st_m1 = max(today, agenda[m1]["data"])
            fi_m1 = fim_norm(st_m1, (0.0 if agenda[m1]["ferramental"]==fg else r["setup (min)"]) + (r["tempo unitário (min)"]*r["quantidade"]))
            st_m2 = max(today, agenda[m2]["data"])
            fi_m2 = fim_norm(st_m2, (0.0 if agenda[m2]["ferramental"]==fg else r["setup (min)"]) + (r["tempo unitário (min)"]*r["quantidade"]))
            
            maq_ch = m1 if fi_m1 <= fi_m2 else m2
            agenda[maq_ch]["data"] = fi_m1 if maq_ch == m1 else fi_m2
            agenda[maq_ch]["ferramental"] = fg
            
            maq_aloc.append(maq_ch); d_fim.append(agenda[maq_ch]["data"]); h_tot.append(round((r["tempo unitário (min)"] * r["quantidade"]) / 60, 2))

        df_editado["Máquina"] = maq_aloc
        df_editado["Fim"] = d_fim
        df_editado["Total (Horas)"] = h_tot
        
        st.write("## 📊 Ocupação Real")
        fig = px.bar(df_editado, x="Máquina", y="Total (Horas)", color="ferramental_grupo", barmode="stack")
        st.plotly_chart(fig, use_container_width=True)

elif menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
