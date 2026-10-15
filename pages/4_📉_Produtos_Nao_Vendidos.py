import streamlit as st

from utils.analise import obter_produtos_nao_vendidos
from utils.processamento import carregar_df_cadastro, carregar_df_vendas
from utils.sessao import inicializar_app, validar_df
from utils.visualizacao import mostrar_paginado

st.set_page_config(page_title="Produtos Não Vendidos", layout="wide")
inicializar_app()
st.title("📉 Produtos Não Vendidos")
df_vendas = validar_df("df_vendas", carregar_df_vendas)
df_cadastro = validar_df("df_cadastro", carregar_df_cadastro)

colunas = st.multiselect(
    "Colunas para exibir:", options=list(df_cadastro.columns), default=list(df_cadastro.columns)
)
df_nao_vendidos = obter_produtos_nao_vendidos(df_vendas, df_cadastro)
if df_nao_vendidos.empty:
    st.info("✅ Todos os produtos foram vendidos no período.")
elif not colunas:
    st.info("Selecione ao menos uma coluna para visualizar os produtos não vendidos.")
else:
    mostrar_paginado(df_nao_vendidos[colunas], "produtos_nao_vendidos")
