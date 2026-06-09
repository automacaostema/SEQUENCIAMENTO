# Antes de aplicar a função, tratamos a coluna de tempo para garantir que seja número
    def converter_tempo(val):
        try:
            if isinstance(val, (pd.Timestamp, pd.Timedelta)):
                return val.hour * 60 + val.minute + val.second / 60
            return float(val)
        except:
            return 0.0

    df_pcp['tempo_unitario'] = df_pcp['tempo_unitario'].apply(converter_tempo)

    def calcular_sequenciamento(row):
        desenho_alvo = str(row['numero_desenho']).strip()
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == desenho_alvo]
        
        if not filtro.empty:
            ferramentas_str = str(filtro['ferramentas_necessarias'].values[0])
            ferramentas = [f.strip().lower() for f in ferramentas_str.split(',')]
            
            # Ajuste de busca
            df_tempos_clean = df_tempos.copy()
            df_tempos_clean['nome_ferramenta_lower'] = df_tempos_clean['nome_ferramenta'].str.lower()
            tempo_setup = df_tempos_clean[df_tempos_clean['nome_ferramenta_lower'].isin(ferramentas)]['tempo_montagem'].sum()
            
            return float(tempo_setup) + (float(row['tempo_unitario']) * float(row['quantidade']))
        return 0

    df_pcp['tempo_total_os'] = df_pcp.apply(calcular_sequenciamento, axis=1)
    st.success("Sequenciamento processado!")
    st.dataframe(df_pcp)
