import streamlit as st
import pandas as pd
import altair as alt
from typing import Tuple, Optional
from utils.processamento import calcular_vendas_agrupadas, adicionar_nomes_produtos, carregar_df_vendas, carregar_df_cadastro
from utils.moeda import formatar_moeda_brasileira
from utils.sessao import inicializar_app, validar_df

inicializar_app()

@st.cache_data
def preparar_produtos(df_vendas: pd.DataFrame, df_cadastro: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula e formata DataFrame de produtos vendidos.
    Retorna DataFrame com colunas: Produto, Quantidade, TotalItem (float), TotalFormatado
    """
    # Agrega e junta nomes
    df = calcular_vendas_agrupadas(df_vendas)
    df = adicionar_nomes_produtos(df, df_cadastro)
    # Renomeia e ordena
    df = df.rename(columns={"ProNom": "Produto"})
    df = df.sort_values(by="TotalItem", ascending=False)
    # Formatação
    df["TotalFormatado"] = df["TotalItem"].map(formatar_moeda_brasileira)
    return df

# -------- Interface de Streamlit --------

st.set_page_config(page_title="Produtos Vendidos", layout="wide")
st.title("📦 Produtos Vendidos")

df_vendas = validar_df("df_vendas", carregar_df_vendas)
df_cadastro = validar_df("df_cadastro", carregar_df_cadastro)

# Preparar produtos vendidos

df_produtos = preparar_produtos(df_vendas, df_cadastro)

# Exibição da tabela completa

st.markdown("### 📝 Lista de Produtos Vendidos")
st.dataframe(
    df_produtos[["Produto", "Quantidade", "TotalFormatado"]]
    .rename(columns={"Quantidade": "Qtd Vendida", "TotalFormatado": "Total R$"}),
    use_container_width=True
)

# Selecionar Top N

top_n = st.slider("Número de produtos no Top", min_value=5, max_value=100, value=10)
top_df = df_produtos.head(top_n)

# Gráfico Top N produtos

st.markdown(f"### 📊 Top {top_n} Produtos por Valor Vendido")
bar_chart = (
    alt.Chart(top_df)
    .mark_bar()
    .encode(
        x=alt.X("TotalItem:Q", title="Total Vendido"),
        y=alt.Y("Produto:N", sort="-x", title="Produto"),
        tooltip=[
            alt.Tooltip("Produto", title="Produto"),
            alt.Tooltip("Quantidade:Q", title="Qtd Vendida"),
            alt.Tooltip("TotalItem:Q", title="Total Vendido", format=",.2f")
        ],
        color=alt.Color("TotalItem:Q", scale=alt.Scale(scheme="greens"), legend=None)
    )
    .properties(height=400)
)

st.altair_chart(bar_chart, use_container_width=True)
