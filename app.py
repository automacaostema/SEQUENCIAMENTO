import streamlit as st
import pandas as pd

st.title("🔍 Diagnóstico da Planilha")

uploaded_file = st.file_uploader("Suba a planilha do PCP", type=["xlsx", "csv"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        
        # Mostra as colunas encontradas para verificarmos se batem com o que esperamos
        st.write("### Colunas encontradas no arquivo:")
        st.write(df.columns.tolist())
        
        # Mostra as primeiras linhas
        st.write("### Primeiras 5 linhas:")
        st.dataframe(df.head())
        
        # Checagem de colunas vitais
        colunas_esperadas = ['codigo interno', 'tempo unidade', 'quantidade', 'data de entrega']
        faltantes = [c for c in colunas_esperadas if c not in df.columns]
        
        if faltantes:
            st.error(f"Faltam as seguintes colunas na sua planilha: {faltantes}")
        else:
            st.success("Todas as colunas necessárias foram encontradas!")
            
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
