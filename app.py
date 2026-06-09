def calcular_sequenciamento(row):
        # Converte o tempo_unitario para numérico (minutos)
        # Se for um objeto de tempo, ele tentará converter para segundos totais
        try:
            tempo_unit = row['tempo_unitario']
            if isinstance(tempo_unit, pd.Timestamp) or isinstance(tempo_unit, pd.Timedelta):
                # Se for formato de hora, converte para minutos totais
                tempo_unit = tempo_unit.hour * 60 + tempo_unit.minute + tempo_unit.second / 60
            else:
                tempo_unit = float(tempo_unit)
        except:
            tempo_unit = 0

        # Desenho
        desenho_alvo = str(row['numero_desenho']).strip()
        filtro = df_desenhos[df_desenhos['numero_desenho'].astype(str).str.strip() == desenho_alvo]
        
        if not filtro.empty:
            ferramentas_str = str(filtro['ferramentas_necessarias'].values[0])
            ferramentas = [f.strip().lower() for f in ferramentas_str.split(',')]
            
            df_tempos['nome_ferramenta_lower'] = df_tempos['nome_ferramenta'].str.lower()
            tempo_setup = df_tempos[df_tempos['nome_ferramenta_lower'].isin(ferramentas)]['tempo_montagem'].sum()
            
            return tempo_setup + (tempo_unit * row['quantidade'])
        return 0
