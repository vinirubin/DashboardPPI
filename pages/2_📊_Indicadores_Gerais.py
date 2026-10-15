import pandas as pd
import streamlit as st

from utils.analise import agrupar_tabelas_temporais, dividir_seguro, filtrar_clientes_identificados
from utils.cache import cache_calculo
from utils.moeda import formatar_moeda_brasileira
from utils.processamento import processa_df_venda_agrupado
from utils.sessao import inicializar_app, validar_df

st.set_page_config(page_title="Indicadores de Vendas", layout="wide")
inicializar_app()
st.title("📊 Indicadores Gerais de Vendas")
df = validar_df("df_vendas_agrupado", processa_df_venda_agrupado)

if st.checkbox("Ignorar cliente não identificado (ID 99999)", value=True):
    df = filtrar_clientes_identificados(df)
if df.empty:
    st.info(
        "Nenhuma venda corresponde ao filtro atual. Desmarque o filtro para ver todas as vendas."
    )

total_clientes = df["Cliente"].nunique()
total_vendas = df["TotalVenda"].sum()
col1, col2, col3 = st.columns(3)
col1.metric("Total de Clientes", total_clientes)
col2.metric("Total Vendido", formatar_moeda_brasileira(total_vendas))
col3.metric(
    "Média de Vendas/Cliente",
    formatar_moeda_brasileira(dividir_seguro(total_vendas, total_clientes)),
)

agrupar_em_cache = cache_calculo(agrupar_tabelas_temporais)


def exibir_tabela(tabela: pd.DataFrame, titulo: str) -> None:
    if tabela.empty:
        st.info(f"Nenhum dado disponível para '{titulo}'.")
        return
    exibicao = tabela.copy()
    for coluna in ("TotalVenda", "MediaPorCliente", "MediaPorVenda"):
        exibicao[coluna] = exibicao[coluna].map(formatar_moeda_brasileira)
    st.markdown(f"### 📈 {titulo}")
    st.dataframe(exibicao, hide_index=True, width="stretch")


nomes = ["Ano", "Semestre", "Trimestre", "Mês", "Semana", "Dia da Semana", "Data"]
for nome, tabela in zip(nomes, agrupar_em_cache(df), strict=True):
    with st.expander(f"Detalhamento por {nome}"):
        exibir_tabela(tabela, nome)
