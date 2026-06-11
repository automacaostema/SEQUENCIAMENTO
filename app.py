# --- Inicialização da Agenda ---
        today = dt.date.today()
        m_list = ["Torno GL 170G - 1", "Torno GL 170G - 2", "Torno Centur - 1", "Torno Centur - 2"]
        
        # Garante que TODAS as máquinas existam no dicionário
        agenda = {}
        for m in m_list:
            agenda[m] = {"data": today, "ferramental": ""}

        maq_aloc, d_ini, d_fim, st_ent, set_reais, h_tot = [], [], [], [], [], []
        items = df_seq.to_dict("records")

        for r in items:
            fg = str(r["ferramental_grupo"])
            is_gl = "8" in fg or "9" in fg
            # Define o grupo da máquina
            g_maq = "Torno GL 170G" if is_gl else "Torno Centur"
            m1 = f"{g_maq} - 1"
            m2 = f"{g_maq} - 2"
            
            # --- Cálculo para M1 ---
            st_m1 = max(today, agenda[m1]["data"])
            se_m1 = float(r["setup (min)"]) if agenda[m1]["ferramental"] != fg else 0.0
            t_u = r["tempo unitário (min)"]
            mi_m1 = se_m1 + (t_u * r["quantidade"])
            fi_m1 = fim_norm(st_m1, mi_m1)

            # --- Cálculo para M2 ---
            st_m2 = max(today, agenda[m2]["data"])
            se_m2 = float(r["setup (min)"]) if agenda[m2]["ferramental"] != fg else 0.0
            mi_m2 = se_m2 + (t_u * r["quantidade"])
            fi_m2 = fim_norm(st_m2, mi_m2)

            # Escolha da máquina com menor data de fim
            if fi_m1 <= fi_m2:
                maq_ch, st_date, ed_date, se_at, mi_fi = m1, st_m1, fi_m1, se_m1, mi_m1
            else:
                maq_ch, st_date, ed_date, se_at, mi_fi = m2, st_m2, fi_m2, se_m2, mi_m2
