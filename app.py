import streamlit as st
from supabase import create_client
import pandas as pd

st.title("🛡️ Painel de Segurança (Somente Leitura)")

sec = st.secrets
client = create_client(sec["SUPABASE_URL"], sec["SUPABASE_KEY"])

if st.button("Verificar Tabela Tempos"):
    res = client.table("tabela_tempos").select("*").execute()
    st.write("Dados em tabela_tempos:", pd.DataFrame(res.data))

if st.button("Verificar Tabela Desenhos"):
    res = client.table("tabela_desenhos").select("*").execute()
    st.write("Dados em tabela_desenhos:", pd.DataFrame(res.data))
