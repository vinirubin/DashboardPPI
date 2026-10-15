import altair as alt
import streamlit as st

from utils.analise import calcular_metricas_clientes, dividir_seguro, filtrar_clientes_identificados
from utils.cache import cache_calculo
from utils.moeda import formatar_moeda_brasileira
from utils.processamento import processa_df_venda_agrupado
from utils.sessao import inicializar_app, validar_df
from utils.visualizacao import mostrar_paginado

st.set_page_config(page_title="Dados dos Clientes", layout="wide")
inicializar_app()
st.title("👥 Análise de Clientes")
df = validar_df("df_vendas_agrupado", processa_df_venda_agrupado)

if st.checkbox("Ignorar cliente 99999", value=True):
    df = filtrar_clientes_identificados(df)
if df.empty:
    st.info("Nenhum cliente corresponde ao filtro atual.")

metricas_em_cache = cache_calculo(calcular_metricas_clientes)
total, retornaram, df_clientes = metricas_em_cache(df)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Clientes", total)
col2.metric("Clientes Retornaram", retornaram)
col3.metric("Taxa de Retorno", f"{dividir_seguro(retornaram * 100, total):.1f}%")
col4.metric("Compras Totais", len(df))

st.markdown("### 📋 Perfil dos Clientes")
df_clientes = df_clientes.sort_values("total_vendas", ascending=False)
exibicao = df_clientes.copy()
exibicao["total_vendas"] = exibicao["total_vendas"].map(formatar_moeda_brasileira)
exibicao["ticket_medio"] = exibicao["ticket_medio"].map(formatar_moeda_brasileira)
mostrar_paginado(
    exibicao.rename(
        columns={
            "total_vendas": "Total Vendido",
            "num_compras": "Compras",
            "ticket_medio": "Ticket Médio",
            "itens_totais": "Linhas de Produtos",
            "unidades_totais": "Unidades",
            "num_retornos": "Retornos",
        }
    ),
    "clientes",
)

st.markdown("### 📊 Top Clientes por Valor Vendido")
top_n = st.slider("Top N Clientes", min_value=5, max_value=50, value=10, step=1)
chart = (
    alt.Chart(df_clientes.head(top_n))
    .mark_bar()
    .encode(
        x=alt.X("total_vendas:Q", title="Total Vendido"),
        y=alt.Y("Cliente:N", sort="-x", title="Cliente"),
        color=alt.Color("total_vendas:Q", scale=alt.Scale(scheme="blues"), legend=None),
        tooltip=[
            alt.Tooltip("Cliente:N", title="Cliente"),
            alt.Tooltip("num_compras:Q", title="Compras"),
            alt.Tooltip("num_retornos:Q", title="Retornos"),
            alt.Tooltip("ticket_medio:Q", title="Ticket Médio", format=",.2f"),
        ],
    )
    .properties(height=400, title=f"Top {top_n} Clientes por Valor Vendido")
)
st.altair_chart(chart, use_container_width=True)
