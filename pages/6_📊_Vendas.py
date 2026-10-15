import streamlit as st

from utils.analise import calcular_vendas_por_localizacao
from utils.cache import cache_calculo
from utils.processamento import processa_df_venda_agrupado
from utils.sessao import inicializar_app, validar_df

st.set_page_config(page_title="Indicadores de Vendas", layout="wide")
inicializar_app()
st.title("📊 Indicadores de Vendas")
df = validar_df("df_vendas_agrupado", processa_df_venda_agrupado)

st.subheader("📈 Métricas Gerais")
col1, col2 = st.columns(2)
col1.metric("Linhas de Produtos por Venda (média)", f"{df['QuantidadeItens'].mean():.2f}")
col2.metric("Unidades por Venda (média)", f"{df['QuantidadeUnidades'].mean():.2f}")

st.subheader("📍 Vendas por Local de Entrega")
localizacao_em_cache = cache_calculo(calcular_vendas_por_localizacao)
df_bairro = localizacao_em_cache(df, "Bairro")
if df_bairro.empty:
    st.info("Não há bairros informados para analisar o local de entrega.")
else:
    st.dataframe(
        df_bairro[["Bairro", "Vendas", "ValorTotalFormatado"]],
        hide_index=True,
        width="stretch",
    )
