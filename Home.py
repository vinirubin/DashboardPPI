import streamlit as st

from utils.sessao import inicializar_app

st.set_page_config(page_title="Sistema de Análise Vendas", layout="wide")
inicializar_app()
st.title("📦 Sistema de Análise Vendas")
st.markdown("""
Bem-vindo ao aplicativo de análise de vendas!

Navegue pelo dashboard usando a barra lateral. Na página **Carregar Arquivos**,
configure e recarregue os arquivos locais do servidor.

Por padrão, o sistema busca CSVs no diretório `dados/` do projeto:

- `NotasFW_ProdInfo.csv`: dados de vendas.
- `prodMercado.csv`: cadastro de produtos.

Use UTF-8, separador **ponto e vírgula** e números com **ponto decimal**.
Datas aceitas: **AAAA-MM-DD** ou **DD/MM/AAAA**. Os códigos são preservados como texto.
Os arquivos são validados antes de substituir os dados da sessão.
""")
