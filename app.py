elif menu == "🔧 Tabela Tempos":
    st.title("🔧 Configuração de Tempos")
    df_t_ed = st.data_editor(df_tempos, use_container_width=True, num_rows="dynamic")
    if st.button("💾 Atualizar Banco (Tempos)"):
        dict_t = df_t_ed.to_dict(orient="records")
        client.table("tabela_tempos").upsert(dict_t).execute()
        invalidar_cache()
        st.success("Banco de Tempos Atualizado!")
        st.rerun()

elif menu == "📐 Tabela Desenhos":
    st.title("📐 Configuração de Desenhos")
    df_d_ed = st.data_editor(df_desenhos, use_container_width=True, num_rows="dynamic")
    if st.button("💾 Atualizar Banco (Desenhos)"):
        dict_d = df_d_ed.to_dict(orient="records")
        client.table("tabela_desenhos").upsert(dict_d).execute()
        invalidar_cache()
        st.success("Banco de Desenhos Atualizado!")
        st.rerun()
