import streamlit as st

from utils.processamento import carregar_df_vendas
from utils.sessao import inicializar_app, validar_df
from utils.visualizacao import mostrar_paginado

st.set_page_config(page_title="df_vendas", layout="wide")
inicializar_app()
st.title("📋 DataFrame de Vendas (Original)")
mostrar_paginado(validar_df("df_vendas", carregar_df_vendas), "df_vendas")
