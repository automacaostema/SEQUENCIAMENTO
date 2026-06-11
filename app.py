elif menu == "🚀 Sequenciamento":
    st.write("### 🚀 Sequenciamento PCP")
    up = st.file_uploader("Planilha", type=["xlsx", "csv"])
    if up:
        df_raw = pd.read_excel(up)
        df_raw.columns = [c.strip() for c in df_raw.columns]
        
        # Carrega dados do banco para calcular
        df_tempos, df_desenhos = carregar_dados()
        
        # Processamento
        df_raw["tempo unitário (min)"] = df_raw["tempo unidade"].apply(limpar_tempo)
        df_raw["quantidade"] = pd.to_numeric(df_raw["quantidade"], errors="coerce").fillna(0)
        
        # Cálculo de setup (usando a função que você já tinha)
        def calc_setup_local(cod):
            if df_desenhos.empty: return 0.0, "sem_ferramenta"
            c_str = str(cod).strip()
            f = df_desenhos[df_desenhos["numero_desenho"].astype(str).str.strip() == c_str]
            if f.empty: return 0.0, "sem_ferramenta"
            f_str = str(f["ferramentas_necessarias"].values[0])
            tot = sum(df_tempos[df_tempos["nome_ferramenta"].str.lower() == ft.strip().lower()]["tempo_montagem"].sum() for ft in f_str.split(","))
            return tot, f_str

        res = df_raw["codigo interno"].apply(calc_setup_local)
        df_raw["setup (min)"], df_raw["ferramental_grupo"] = zip(*res)
        
        # Ordenação e Exibição
        df_raw = df_raw.sort_values(by=["data de entrega", "ferramental_grupo"]).copy()
        df_raw["Ordem"] = range(1, len(df_raw) + 1)
        
        st.write("### ✏️ Sequenciamento Manual")
        df_editado = st.data_editor(df_raw, use_container_width=True)
        st.write("Processamento concluído com base nos dados do banco.")
