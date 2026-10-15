"""Executa as páginas originais somente com os dados gerados para apresentação."""

import sys
from pathlib import Path

import streamlit as st

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(PASTA))

from gerar_dados_demo import gerar_dados  # noqa: E402

from utils.processamento import agrupar_vendas_por_controle  # noqa: E402

st.set_page_config(page_title="DashboardPPI | Demonstração", layout="wide")

if "_dados_demo" not in st.session_state:
    vendas, cadastro = gerar_dados()
    st.session_state.update(
        df_vendas=vendas,
        df_cadastro=cadastro,
        df_vendas_agrupado=agrupar_vendas_por_controle(vendas),
        caminho_vendas="DEMONSTRAÇÃO: dados gerados em memória",
        caminho_cadastro="DEMONSTRAÇÃO: dados gerados em memória",
        _dados_demo=True,
    )

st.info("DADOS FICTÍCIOS • Demonstração pública do DashboardPPI. Todos os valores são sintéticos.")
st.sidebar.caption("DashboardPPI · apresentação")
st.sidebar.info("Dados sintéticos\n\nProdutos, clientes, regiões e valores fictícios.")


def pagina(prefixo: str, titulo: str, url: str, icone: str):
    arquivo = next((RAIZ / "pages").glob(f"{prefixo}*.py"))
    return st.Page(arquivo, title=titulo, url_path=url, icon=icone)


menu = st.navigation(
    [
        st.Page(RAIZ / "Home.py", title="Visão inicial", icon="🏠", default=True),
        pagina("2_", "Indicadores gerais", "indicadores", "📊"),
        pagina("3_", "Produtos vendidos", "produtos", "📦"),
        pagina("4_", "Produtos não vendidos", "nao-vendidos", "📉"),
        pagina("5_", "Clientes", "clientes", "👥"),
        pagina("6_", "Vendas por região", "regioes", "📍"),
    ]
)
menu.run()
st.caption("Demonstração com dados sintéticos · não representa o conjunto comercial analisado.")
