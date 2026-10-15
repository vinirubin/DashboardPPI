import altair as alt
import streamlit as st

from utils.analise import (
    MAX_LINHAS_GRAFICO,
    PERIODOS,
    detalhar_giro_vendas,
    limitar_grafico_giro,
    preparar_produtos,
)
from utils.cache import cache_calculo
from utils.processamento import carregar_df_cadastro, carregar_df_vendas
from utils.sessao import inicializar_app, validar_df
from utils.visualizacao import mostrar_paginado

st.set_page_config(page_title="Produtos Vendidos", layout="wide")
inicializar_app()
st.title("📦 Produtos Vendidos")
df_vendas = validar_df("df_vendas", carregar_df_vendas)
df_cadastro = validar_df("df_cadastro", carregar_df_cadastro)

preparar_em_cache = cache_calculo(preparar_produtos)
giro_em_cache = cache_calculo(detalhar_giro_vendas)
df_produtos = preparar_em_cache(df_vendas, df_cadastro)
st.markdown("### 📝 Lista de Produtos Vendidos")
mostrar_paginado(
    df_produtos[["ProCod", "Produto", "Quantidade", "TotalFormatado"]].rename(
        columns={"Quantidade": "Qtd Vendida", "TotalFormatado": "Total R$"}
    ),
    "produtos_vendidos",
)

top_n = st.slider("Número de produtos no Top", min_value=5, max_value=100, value=10)
top_df = df_produtos.head(top_n)
st.markdown(f"### 📊 Top {top_n} Produtos por Valor Vendido")
bar_chart = (
    alt.Chart(top_df)
    .mark_bar()
    .encode(
        x=alt.X("TotalItem:Q", title="Total Vendido"),
        y=alt.Y("RotuloProduto:N", sort="-x", title="Produto"),
        tooltip=[
            alt.Tooltip("ProCod:N", title="Código"),
            alt.Tooltip("Produto:N", title="Produto"),
            alt.Tooltip("Quantidade:Q", title="Qtd Vendida"),
            alt.Tooltip("TotalItem:Q", title="Total Vendido", format=",.2f"),
        ],
        color=alt.Color("TotalItem:Q", scale=alt.Scale(scheme="greens"), legend=None),
    )
    .properties(height=400)
)
st.altair_chart(bar_chart, use_container_width=True)

st.markdown("### 🔄 Giro de Venda por Período")
periodo = st.selectbox("Selecionar período de detalhamento:", list(PERIODOS))
df_giro = giro_em_cache(df_vendas, df_cadastro, periodo)
mostrar_paginado(
    df_giro.drop(columns="RotuloProduto").rename(
        columns={"Periodo": "Período", "Quantidade": "Qtd Vendida"}
    ),
    "giro_vendas",
)
dados_grafico = limitar_grafico_giro(df_giro)
if len(df_giro) > MAX_LINHAS_GRAFICO:
    st.info(
        f"O gráfico mostra as {MAX_LINHAS_GRAFICO} combinações de produto e período "
        "com maior quantidade vendida. A tabela e o download contêm todos os registros."
    )
grafico = (
    alt.Chart(dados_grafico)
    .mark_bar()
    .encode(
        x=alt.X("Quantidade:Q", title="Qtd Vendida"),
        y=alt.Y("RotuloProduto:N", sort="-x", title="Produto"),
        color=alt.Color("Periodo:N", legend=alt.Legend(title="Período")),
        tooltip=["Periodo", "ProCod", "Produto", "Quantidade"],
    )
    .properties(height=500)
)
st.altair_chart(grafico, use_container_width=True)
