# 4. ORGANIZAR SEQUÊNCIA (Algoritmo de Prioridade)
    # Primeiro, buscamos o ferramental de cada item para agrupar
    def buscar_ferramental(row):
        cod = str(row['numero_desenho']).strip()
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == cod]
        if not filtro.empty:
            return str(filtro['ferramentas_necessarias'].values[0])
        return "sem_ferramenta"

    df_pcp['ferramental_grupo'] = df_pcp.apply(buscar_ferramental, axis=1)

    # Ordenação Inteligente:
    # 1. Data de entrega (mais perto primeiro)
    # 2. Ferramental (agrupa itens iguais)
    # 3. Tempo total (menor primeiro)
    df_sequenciado = df_pcp.sort_values(
        by=['data de entrega', 'ferramental_grupo', 'tempo_total_os'], 
        ascending=[True, True, True]
    )
    
    st.success("Sequenciamento inteligente organizado!")
    st.dataframe(df_sequenciado)
