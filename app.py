import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")
st.title("🚀 PCP Stema")

sec = st.secrets
client = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])

# --- FUNÇÕES ---
def limpar_tempo(val):
    if hasattr(val, "hour"): return val.hour * 60 + val.minute
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        try:
            p = [float(x) for x in val.split(":")]
            if len(p) == 3: return p[0]*60 + p[1] + (p[2]/60.0)
            if len(p) == 2: return p[0] + (p[1]/60.0)
            return float(p[0])
        except: return 0.0
    return 0.0

def fim_norm(ini, mins):
    data = ini
    while mins > 0:
        if mins <= 450: mins = 0
        else:
            mins -= 450
            data += dt.timedelta(days=1)
            while data.weekday() >= 5: data += dt.timedelta(days=1)
    return data

def calc_setup(cod, df_t, df_d):
    f = df_d[df_d["numero_desenho"].astype(str).str.strip() == str(cod).strip()]
    if f.empty: return 0.0, "sem_ferramenta"
    f_str = str(f["ferramentas_necessarias"].values[0])
    tot = 0.0
    for ft in f_str.split(","):
        tot += df_t[df_t["nome_ferramenta"].str.lower() == ft.strip().lower()]["tempo_montagem"].sum()
    return tot, f_str

def salvar_banco(tabela, df):
    records = df.replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
    for r in records:
        if "id" in r and (r["id"] is None or pd.isna(r["id"])): del r["id"]
    client.table(tabela).upsert(records).execute()
    st.success("Salvo com sucesso!")
    st.rerun()

# --- MENU ---
menu = st.sidebar.radio("Navegação", ["🚀 Sequenciamento", "🔧 Tabela Tempos", "📐 Tabela Desenhos"])

# --- LÓGICA DO PCP ---
if menu == "🚀 Sequenciamento":
    up = st.file_uploader("Upload Planilha", type=["xlsx", "csv"])
    if up:
        df_raw = pd.read_excel(up)
        df_raw.columns = [c.strip() for c in df_raw.columns]
        
        # Carrega dados do banco
        df_tempos = pd.DataFrame(client.table("tabela_tempos").select("*").execute().data)
        df_desenhos = pd.DataFrame(client.table("tabela_desenhos").select("*").execute().data)
        
        # Processamento
        df_raw["tempo unitário (min)"] = df_raw["tempo unidade"].apply(limpar_tempo)
        res = [calc_setup(c, df_tempos, df_desenhos) for c in df_raw["codigo interno"]]
        df_raw["setup (min)"], df_raw["ferramental_grupo"] = zip(*res)
        df_raw = df_raw.sort_values(by=["data de entrega", "ferramental_grupo"]).copy()
        df_raw["Ordem"] = range(1, len(df_raw) + 1)
        
        df_edit = st.data_editor(df_raw, disabled=[c for c in df_raw.columns if c != "Ordem"], use_container_width=True)
        
        # Cálculo de Ocupação
        today = dt.date.today()
        m_list = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
        agenda = {m: {"data": today, "ferramental": ""} for m in m_list}
        
        res_lista = []
        for r in df_edit.to_dict("records"):
            fg = str(r["ferramental_grupo"])
            g_maq = "Torno GL 170G" if ("8" in fg or "9" in fg) else "Torno Centur"
            
            # Balanceamento entre máquinas do mesmo grupo
            maqs = [f"{g_maq} - 1", f"{g_maq} - 2"]
            possiveis = []
            for m in maqs:
                st_m = max(today, agenda[m]["data"])
                se_m = float(r["setup (min)"]) if agenda[m]["ferramental"] != fg else 0.0
                mi_m = se_m + (r["tempo unitário (min)"] * r["quantidade"])
                possiveis.append({"nome": m, "fim": fim_norm(st_m, mi_m), "st": st_m, "se": se_m, "mi": mi_m})
            
            melhor = min(possiveis, key=lambda x: x["fim"])
            lim = pd.to_datetime(r["data de entrega"]).date()
            status = "✅ No Prazo" if melhor["fim"] <= lim else ("⚡ Sobrecarga" if lim >= today else "⚠️ ATRASADO")
            
            agenda[melhor["nome"]].update({"data": melhor["fim"], "ferramental": fg})
            res_lista.append({**r, "Máquina": melhor["nome"], "Início": melhor["st"], "Fim": melhor["fim"], 
                              "Status": status, "setup (min)": melhor["se"], "Total (Horas)": round(melhor["mi"]/60, 2)})

        df_seq = pd.DataFrame(res_lista)
        df_seq["Mês/Ano"] = pd.to_datetime(df_seq["Fim"]).dt.to_period("M").astype(str)

        # Gráfico
        st.write("## 📊 Ocupação Real")
        df_mes = df_seq.groupby(["Mês/Ano", "Máquina"])["Total (Horas)"].sum().reset_index()
        fig = px.bar(df_mes, x="Mês/Ano", y="Total (Horas)", facet_col="Máquina", facet_col_wrap=2, barmode="stack")
        st.plotly_chart(fig, use_container_width=True)

        # Filas
        st.write("## 🗓️ Filas de Trabalho")
        col_ordem = ["codigo interno", "n servico", "Status", "data de entrega", "Início", "Fim", "quantidade", "setup (min)", "Total (Horas)", "ferramental_grupo"]
        for maq in m_list:
            with st.expander(f"Fila: {maq}"):
                df_m = df_seq[df_seq["Máquina"] == maq][col_ordem]
                st.dataframe(df_m, use_container_width=True)

# --- TABELAS ---
elif menu in ["🔧 Tabela Tempos", "📐 Tabela Desenhos"]:
    tabela = "tabela_tempos" if menu == "🔧 Tabela Tempos" else "tabela_desenhos"
    df = pd.DataFrame(client.table(tabela).select("*").execute().data)
    df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar"): salvar_banco(tabela, df_edit)
