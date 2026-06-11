def limpar_tempo(val):
    # Log para ver o que está chegando
    if pd.isna(val) or val == 0: return 0.0
    
    if hasattr(val, "hour"): return val.hour * 60 + val.minute
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        try:
            p = [float(x) for x in val.split(":")]
            if len(p) == 3: return p[0] * 60 + p[1] + (p[2] / 60.0)
            if len(p) == 2: return p[0] + (p[1] / 60.0)
            return float(p[0])
        except: 
            return 0.0
    return 0.0

def calc_setup(cod):
    if df_desenhos.empty: return 0.0, "sem_ferramenta"
    
    c_str = str(cod).strip()
    mask = df_desenhos["numero_desenho"].astype(str).str.strip() == c_str
    f = df_desenhos[mask]
    
    if f.empty: 
        # Isso imprime se o código não for achado na tabela desenhos
        return 0.0, f"NÃO ACHOU {c_str}"
        
    f_str = str(f["ferramentas_necessarias"].values[0])
    
    # Soma dos tempos
    tot = 0.0
    for ft in f_str.split(","):
        ft_clean = ft.strip().lower()
        # Procura na tabela tempos
        match = df_tempos[df_tempos["nome_ferramenta"].str.lower() == ft_clean]
        if not match.empty:
            tot += match["tempo_montagem"].sum()
        else:
            # Se não achou a ferramenta na tabela tempos
            st.warning(f"Ferramenta {ft_clean} não encontrada na tabela de tempos!")
            
    return tot, f_str
