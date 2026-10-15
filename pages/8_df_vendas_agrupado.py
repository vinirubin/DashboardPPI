import streamlit as st

from utils.processamento import processa_df_venda_agrupado
from utils.sessao import inicializar_app, validar_df
from utils.visualizacao import mostrar_paginado

st.set_page_config(page_title="df_vendas_agrupado", layout="wide")
inicializar_app()
st.title("📋 DataFrame de Vendas (Agrupado)")
mostrar_paginado(validar_df("df_vendas_agrupado", processa_df_venda_agrupado), "df_vendas_agrupado")
