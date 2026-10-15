"""Transformações puras e adaptadores compatíveis com as páginas existentes."""

import pandas as pd

from utils.constantes import DIAS_SEMANA_PT
from utils.dados import (
    ErroDados,
    FonteCSV,
    ler_cadastro,
    ler_vendas,
    normalizar_cadastro,
    validar_colunas,
)


def adicionar_periodos(df: pd.DataFrame) -> pd.DataFrame:
    resultado = df.copy()
    datas = resultado["Data"].dt
    resultado["Ano"] = datas.year
    resultado["Semestre"] = (
        datas.year.astype(str) + " - S" + ((datas.month - 1) // 6 + 1).astype(str)
    )
    resultado["Trimestre"] = datas.to_period("Q").astype(str)
    resultado["MesPeriodo"] = datas.to_period("M").astype(str)
    resultado["SemanaInicioDt"] = datas.to_period("W-SUN").astype(str)
    resultado["Dia"] = datas.strftime("%Y-%m-%d")
    resultado["DiaSemana"] = datas.day_name().map(DIAS_SEMANA_PT)
    return resultado


def calcular_vendas_agrupadas(df_vendas: pd.DataFrame) -> pd.DataFrame:
    validar_colunas(df_vendas, {"ProCod", "Quantidade", "TotalItem"})
    return df_vendas.groupby("ProCod", as_index=False, observed=True)[
        ["Quantidade", "TotalItem"]
    ].sum()


def adicionar_nomes_produtos(df_vendidos: pd.DataFrame, df_cadastro: pd.DataFrame) -> pd.DataFrame:
    cadastro = normalizar_cadastro(df_cadastro)
    resultado = df_vendidos.drop(columns=["ProNom"], errors="ignore").merge(
        cadastro[["ProCod", "ProNom"]], on="ProCod", how="left", validate="many_to_one"
    )
    resultado["ProNom"] = resultado["ProNom"].fillna(
        "Produto sem cadastro (" + resultado["ProCod"].astype(str) + ")"
    )
    return resultado


def agrupar_vendas_por_controle(df: pd.DataFrame) -> pd.DataFrame:
    validar_colunas(df, {"Controle", "Cliente", "TotalItem", "Data", "ProCod", "Quantidade"})
    # O ERP reutiliza controles em dias diferentes: a venda é DataVenda + Controle.
    datas_venda = df["Data"].dt.normalize().rename("DataVenda")
    consistencia = df.groupby([datas_venda, "Controle"], observed=True)["Cliente"].nunique(
        dropna=False
    )
    if consistencia.gt(1).any():
        raise ErroDados("Há controles associados a clientes diferentes no mesmo dia. Revise o CSV.")
    agregacoes = {
        "Cliente": ("Cliente", "first"),
        "TotalVenda": ("TotalItem", "sum"),
        "Data": ("Data", "min"),
        "QuantidadeItens": ("ProCod", "size"),
        "QuantidadeUnidades": ("Quantidade", "sum"),
    }
    if "Bairro" in df:
        agregacoes["Bairro"] = ("Bairro", "first")
    agrupado = df.groupby([datas_venda, "Controle"], observed=True).agg(**agregacoes).reset_index()
    return adicionar_periodos(agrupado)


def carregar_df_cadastro(caminho: FonteCSV | None = None) -> pd.DataFrame:
    return _carregar_na_sessao("df_cadastro", "caminho_cadastro", caminho, ler_cadastro)


def carregar_df_vendas(caminho: FonteCSV | None = None) -> pd.DataFrame:
    return _carregar_na_sessao(
        "df_vendas", "caminho_vendas", caminho, lambda fonte: adicionar_periodos(ler_vendas(fonte))
    )


def _carregar_na_sessao(nome, chave_caminho, caminho, leitor) -> pd.DataFrame:
    import streamlit as st

    from utils.sessao import carregar_arquivo_na_sessao, invalidar_derivados

    fonte = caminho if caminho is not None else st.session_state.get(chave_caminho)
    if not carregar_arquivo_na_sessao(nome, fonte, leitor, forcar=caminho is not None):
        st.stop()
    if nome == "df_vendas":
        invalidar_derivados()
    return st.session_state[nome]


def processa_df_venda_agrupado() -> pd.DataFrame:
    import streamlit as st

    from utils.sessao import df_em_cache

    if not df_em_cache("df_vendas"):
        carregar_df_vendas()
    try:
        agrupado = agrupar_vendas_por_controle(st.session_state["df_vendas"])
    except ErroDados as exc:
        st.error(str(exc))
        st.stop()
    st.session_state["df_vendas_agrupado"] = agrupado
    return agrupado
