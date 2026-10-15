"""Regras de análise testáveis, sem renderização ou estado global."""

import pandas as pd

from utils.constantes import DIAS_SEMANA_PT
from utils.moeda import formatar_moeda_brasileira
from utils.processamento import (
    adicionar_nomes_produtos,
    adicionar_periodos,
    calcular_vendas_agrupadas,
)

PERIODOS = {
    "Ano": "Ano",
    "Semestre": "Semestre",
    "Trimestre": "Trimestre",
    "Mês": "MesPeriodo",
    "Semana": "SemanaInicioDt",
    "Dia da Semana": "DiaSemana",
    "Data": "Dia",
}
MAX_LINHAS_GRAFICO = 5000


def dividir_seguro(numerador: float, denominador: float) -> float:
    return float(numerador / denominador) if denominador else 0.0


def filtrar_clientes_identificados(df: pd.DataFrame) -> pd.DataFrame:
    identificados = df["Cliente"].astype("string").str.strip().ne("99999").fillna(False)
    return df.loc[identificados].copy()


def ordenar_dias(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    resultado = df.copy()
    resultado[coluna] = pd.Categorical(
        resultado[coluna], categories=list(DIAS_SEMANA_PT.values()), ordered=True
    )
    return resultado.sort_values(coluna, ignore_index=True)


def agrupar_tabelas_temporais(df: pd.DataFrame) -> tuple[pd.DataFrame, ...]:
    tabelas = []
    for titulo, coluna in PERIODOS.items():
        agrupado = df.groupby(coluna, as_index=False, observed=True).agg(
            TotalVenda=("TotalVenda", "sum"),
            QuantClientes=("Cliente", "nunique"),
            QuantVendas=("Controle", "size"),
            MediaPorVenda=("TotalVenda", "mean"),
        )
        agrupado["MediaPorCliente"] = (
            agrupado["TotalVenda"]
            / agrupado["QuantClientes"].where(agrupado["QuantClientes"].ne(0))
        ).fillna(0)
        if titulo == "Dia da Semana":
            agrupado = ordenar_dias(agrupado, coluna)
        if titulo == "Semana":
            meses = (
                df[[coluna, "MesPeriodo"]]
                .rename(columns={"MesPeriodo": "Meses"})
                .drop_duplicates()
                .sort_values("Meses")
                .groupby(coluna, as_index=False, observed=True)["Meses"]
                .agg(" / ".join)
            )
            agrupado = agrupado.merge(meses, on=coluna, validate="one_to_one")
        if titulo in ("Mês", "Semana", "Data"):
            agrupado = agrupado.rename(columns={coluna: titulo})
        tabelas.append(agrupado)
    return tuple(tabelas)


def preparar_produtos(df_vendas: pd.DataFrame, df_cadastro: pd.DataFrame) -> pd.DataFrame:
    df = adicionar_nomes_produtos(calcular_vendas_agrupadas(df_vendas), df_cadastro)
    df = df.rename(columns={"ProNom": "Produto"}).sort_values("TotalItem", ascending=False)
    df["TotalFormatado"] = df["TotalItem"].map(formatar_moeda_brasileira)
    df["RotuloProduto"] = df["Produto"] + " [" + df["ProCod"].astype(str) + "]"
    return df


def detalhar_giro_vendas(
    df_vendas: pd.DataFrame, df_cadastro: pd.DataFrame, periodo: str
) -> pd.DataFrame:
    if periodo not in PERIODOS:
        raise ValueError("Período inválido.")
    coluna = PERIODOS[periodo]
    df = df_vendas if coluna in df_vendas else adicionar_periodos(df_vendas)
    agrupado = (
        df.groupby([coluna, "ProCod"], as_index=False, observed=True)
        .agg(Quantidade=("Quantidade", "sum"))
        .rename(columns={coluna: "Periodo"})
    )
    resultado = adicionar_nomes_produtos(agrupado, df_cadastro).rename(
        columns={"ProNom": "Produto"}
    )
    resultado["RotuloProduto"] = resultado["Produto"] + " [" + resultado["ProCod"].astype(str) + "]"
    return ordenar_dias(resultado, "Periodo") if periodo == "Dia da Semana" else resultado


def limitar_grafico_giro(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) <= MAX_LINHAS_GRAFICO:
        return df
    return df.nlargest(MAX_LINHAS_GRAFICO, "Quantidade")


def obter_produtos_nao_vendidos(df_vendas: pd.DataFrame, df_cadastro: pd.DataFrame) -> pd.DataFrame:
    return df_cadastro.loc[~df_cadastro["ProCod"].isin(df_vendas["ProCod"])].copy()


def calcular_metricas_clientes(df: pd.DataFrame) -> tuple[int, int, pd.DataFrame]:
    agrupado = df.groupby("Cliente", as_index=False, observed=True).agg(
        total_vendas=("TotalVenda", "sum"),
        num_compras=("Controle", "size"),
        itens_totais=("QuantidadeItens", "sum"),
        unidades_totais=("QuantidadeUnidades", "sum"),
    )
    agrupado["ticket_medio"] = (
        agrupado["total_vendas"] / agrupado["num_compras"].where(agrupado["num_compras"].ne(0))
    ).fillna(0)
    agrupado["num_retornos"] = agrupado["num_compras"] - 1
    return len(agrupado), int(agrupado["num_retornos"].gt(0).sum()), agrupado


def calcular_vendas_por_localizacao(df: pd.DataFrame, campo: str) -> pd.DataFrame:
    if campo not in df:
        return pd.DataFrame(columns=[campo, "Vendas", "ValorTotal", "ValorTotalFormatado"])
    agrupado = (
        df.groupby(campo, as_index=False, observed=True)
        .agg(Vendas=("Controle", "size"), ValorTotal=("TotalVenda", "sum"))
        .sort_values("Vendas", ascending=False, ignore_index=True)
    )
    agrupado["ValorTotalFormatado"] = agrupado["ValorTotal"].map(formatar_moeda_brasileira)
    return agrupado
