import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.title("🚛 Simulador Programação")

# Upload do arquivo
uploaded_file = st.file_uploader("Envie a planilha STATUS ATUALIZADO.xlsx", type=["xlsx"])

if uploaded_file:
    try:
        # Detecta automaticamente a aba (única)
        xls = pd.ExcelFile(uploaded_file)
        nome_aba = xls.sheet_names[0]

        resumo = pd.read_excel(xls, sheet_name=nome_aba)
        resumo = resumo.loc[:, ~resumo.columns.str.contains('^Unnamed')]
        resumo.columns = resumo.columns.str.strip()

        # Pré-processamento
        data_hoje = pd.to_datetime("today")
        resumo["VENC. CAP."] = pd.to_datetime(resumo["VENC. CAP."], errors='coerce')
        resumo["Capacitação Válida"] = resumo["VENC. CAP."].apply(lambda x: x >= data_hoje if pd.notnull(x) else False)
        resumo["Tem Pendências"] = resumo["PENDÊNCIAS"].apply(lambda x: False if isinstance(x, str) and x.strip().upper() == "OK" else True)

        # Normalizar TIPO e POSIÇÃO (corrigir espaços e aspas)
        resumo["TIPO"] = resumo["TIPO"].astype(str).str.strip().str.replace("´", "`", regex=False)
        resumo["POSIÇÃO"] = resumo["POSIÇÃO"].astype(str).str.strip().str.upper()
        resumo["c"] = resumo["c"].astype(str).str.strip().str.upper()  # Coluna A que identifica "FO"

        # Filtros laterais principais
        st.sidebar.header("Filtros de Simulação")
        filtro_frota = st.sidebar.selectbox("Tipo de Frota:", options=["Todos"] + list(resumo["Frota"].dropna().unique()))
        filtro_capacitacao = st.sidebar.selectbox("Capacitação:", ["Todos", "Válida", "Vencida"])

        # Segmentação para veículos em manutenção
        veic_manutencao = st.sidebar.checkbox("📋 Veículos em manutenção (FO)")

        # Aplicar filtros
        df = resumo.copy()

        if veic_manutencao:
            df = df[df["c"] == "FO"]
        else:
            if filtro_frota != "Todos":
                df = df[df["Frota"] == filtro_frota]

            if filtro_capacitacao == "Válida":
                df = df[df["Capacitação Válida"] == True]
            elif filtro_capacitacao == "Vencida":
                df = df[df["Capacitação Válida"] == False]

        # Colunas a exibir
        colunas_exibir = ["POSIÇÃO", "PLACA", "TIPO", "PENDÊNCIAS", "Frota"]
        df_exibir = df[colunas_exibir].copy()

        # Mostrar resultados filtrados
        st.subheader("Resultado da Simulação")
        st.dataframe(df_exibir.astype(str))

        # Armazenar simulação como histórico
        historico_path = "simulacoes_historicas"
        os.makedirs(historico_path, exist_ok=True)
        nome_arquivo = f"simulacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df_exibir.to_excel(os.path.join(historico_path, nome_arquivo), index=False)

    except Exception as e:
        st.error(f"❌ Erro ao carregar a planilha: {e}")
else:
    st.info("📎 Por favor, envie a planilha 'STATUS ATUALIZADO.xlsx' para iniciar a simulação.")
