import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

# Conexão
sec = st.secrets
client = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        t = client.table("tabela_tempos").select("*").execute().data
        d = client.table("tabela_desenhos").select("*").execute().data
        return pd.DataFrame(t), pd.DataFrame(d)
    except: return pd.DataFrame(), pd.DataFrame()

df_tempos, df_desenhos = carregar_dados()

def limpar_tempo(val):
    try:
        if isinstance(val, (int, float)): return float(val)
        if isinstance(val, str):
            p = [float(x) for x in val.split(":")]
            return p[0]*60 + p[1] + (p[2]/60.0) if len(p)==3 else (p[0] + p[1]/60.0 if len(p)==2 else float(p[0]))
        return 0.0
    except: return 0.0

def fim_norm(ini, mins):
    data = ini
    rest = int(mins)
    while rest > 0:
        if rest <= 450: rest = 0
        else:
            rest -= 450
            data += dt.timedelta(days=1)
            while data.weekday() >= 5: data += dt.timedelta(days=1)
    return data

menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

if menu == "🚀 Sequenciamento":
    up = st.file_uploader("Planilha", type=["xlsx", "csv"])
    if up:
        df_raw = pd.read_excel(up)
        df_raw.columns = [c.strip() for c in df_raw.columns]
        df_raw["tempo unitário (min)"] = df_raw["tempo unidade"].apply(limpar_tempo)
        df_raw["quantidade"] = pd.to_numeric(df_raw["quantidade"], errors="coerce").fillna(0)
        
        # Setup c/ segurança
        def get_setup(cod):
            f = df_desenhos[df_desenhos["numero_desenho"].astype(str).str.strip() == str(cod).strip()]
            if f.empty: return 0.0, "sem_ferramenta"
            fts = str(f["ferramentas_necessarias"].values[0]).split(",")
            tot = sum(df_tempos[df_tempos["nome_ferramenta"].str.lower() == ft.strip().lower()]["tempo_montagem"].sum() for ft in fts)
            return tot, str(f["ferramentas_necessarias"].values[0])

        df_raw["setup (min)"], df_raw["ferramental_grupo"] = zip(*df_raw["codigo interno"].apply(get_setup))
        df_editado = st.data_editor(df_raw, use_container_width=True)

        # Agenda c/ Blindagem
        today = dt.date.today()
        m_list = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
        agenda = {m: {"data": today, "ferramental": ""} for m in m_list}
        
        res_list = []
        for r in df_editado.to_dict("records"):
            fg = str(r["ferramental_grupo"])
            m_g = "Torno GL 170G" if any(x in fg for x in ["8","9"]) else "Torno Centur"
            m1, m2 = f"{m_g} - 1", f"{m_g} - 2"
            
            # Cálculo de fim
            load = (0.0 if agenda[m1]["ferramental"]==fg else r["setup (min)"]) + (r["tempo unitário (min)"]*r["quantidade"])
            fi_m1 = fim_norm(max(today, agenda[m1]["data"]), load)
            fi_m2 = fim_norm(max(today, agenda[m2]["data"]), load)
            
            maq = m1 if fi_m1 <= fi_m2 else m2
            agenda[maq]["data"] = fi_m1 if maq == m1 else fi_m2
            agenda[maq]["ferramental"] = fg
            r["Máquina"] = maq
            res_list.append(r)
        
        st.write("## 📊 Ocupação Real")
        st.plotly_chart(px.bar(pd.DataFrame(res_list), x="Máquina", y="quantidade", color="ferramental_grupo"))

elif menu == "🔧 Tabela Tempos":
    if st.button("💾 Salvar"):
        client.table("tabela_tempos").upsert(st.data_editor(df_tempos, num_rows="dynamic").to_dict("records"), on_conflict="nome_ferramenta").execute()
        st.rerun()
    else: st.data_editor(df_tempos, num_rows="dynamic")

elif menu == "📐 Tabela Desenhos":
    if st.button("💾 Salvar"):
        client.table("tabela_desenhos").upsert(st.data_editor(df_desenhos, num_rows="dynamic").to_dict("records"), on_conflict="numero_desenho").execute()
        st.rerun()
    else: st.data_editor(df_desenhos, num_rows="dynamic")
