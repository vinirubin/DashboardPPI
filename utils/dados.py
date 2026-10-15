"""Leitura e validação dos contratos CSV, sem dependência da interface."""

from pathlib import Path
from typing import IO

import pandas as pd

from utils.caminho import resolver_caminho

FonteCSV = str | Path | IO
COLUNAS_VENDAS = {"ProCod", "Quantidade", "TotalItem", "Data", "Controle", "Cliente"}
COLUNAS_CADASTRO = {"ProCod", "ProNom"}


class ErroDados(ValueError):
    """Entrada inválida com mensagem adequada à interface, sem dados comerciais."""


def validar_colunas(df: pd.DataFrame, colunas: set[str]) -> None:
    ausentes = colunas.difference(df.columns)
    if ausentes:
        raise ErroDados(f"Colunas obrigatórias ausentes: {', '.join(sorted(ausentes))}.")


def _ler_csv(fonte: FonteCSV) -> pd.DataFrame:
    origem = resolver_caminho(fonte) if isinstance(fonte, (str, Path)) else fonte
    posicao = None
    try:
        if not isinstance(origem, Path) and not origem.seekable():
            raise ErroDados("A fonte CSV deve permitir reposicionamento para validação.")
        if hasattr(origem, "seek") and origem.seekable():
            posicao = origem.tell()
            origem.seek(0)
        cabecalho = (
            pd.read_csv(
                origem,
                sep=";",
                encoding="utf-8-sig",
                dtype="string",
                keep_default_na=False,
                header=None,
                nrows=1,
            )
            .iloc[0]
            .str.strip()
        )
        if cabecalho.duplicated().any():
            raise ErroDados("O CSV contém nomes de colunas duplicados.")
        if posicao is not None:
            origem.seek(0)
        df = pd.read_csv(
            origem, sep=";", encoding="utf-8-sig", dtype="string", keep_default_na=False
        )
    except (OSError, UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise ErroDados(
            "Não foi possível ler o CSV. Verifique acesso, UTF-8 e separador ';'."
        ) from exc
    finally:
        if posicao is not None:
            origem.seek(posicao)
    if df.empty:
        raise ErroDados("O CSV não contém registros.")
    if not isinstance(df.index, pd.RangeIndex):
        raise ErroDados("O CSV contém registros com mais campos que o cabeçalho.")
    df.columns = df.columns.str.strip()
    for coluna in df.columns:
        df[coluna] = df[coluna].str.strip().replace("", pd.NA)
    return df


def _validar_identificadores(df: pd.DataFrame, colunas: tuple[str, ...]) -> None:
    for coluna in colunas:
        if df[coluna].isna().any():
            raise ErroDados(f"A coluna '{coluna}' contém identificadores vazios.")


def ler_vendas(fonte: FonteCSV) -> pd.DataFrame:
    df = _ler_csv(fonte)
    validar_colunas(df, COLUNAS_VENDAS)
    _validar_identificadores(df, ("ProCod", "Controle"))
    for coluna in ("Quantidade", "TotalItem"):
        valores = pd.to_numeric(df[coluna], errors="coerce")
        invalidos = valores.isna() | valores.isin([float("inf"), float("-inf")])
        if invalidos.any():
            raise ErroDados(
                f"A coluna '{coluna}' contém {int(invalidos.sum())} valor(es) inválido(s). "
                "Use números finitos e ponto decimal, sem separador de milhares."
            )
        df[coluna] = valores
    # Reconhecer o formato antes do parse impede a inversão silenciosa de dia/mês.
    horario = r"(?:[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d{1,9})?)?)?"
    formato_valido = (
        df["Data"]
        .str.fullmatch(rf"(?:\d{{4}}-\d{{2}}-\d{{2}}|\d{{2}}/\d{{2}}/\d{{4}}){horario}")
        .fillna(False)
    )
    texto_iso = (
        df["Data"]
        .where(formato_valido)
        .str.replace(r"^(\d{2})/(\d{2})/(\d{4})", r"\3-\2-\1", regex=True)
    )
    datas = pd.to_datetime(texto_iso, format="ISO8601", errors="coerce")
    if datas.isna().any():
        raise ErroDados(
            f"A coluna 'Data' contém {int(datas.isna().sum())} data(s) inválida(s). "
            "Use ISO (AAAA-MM-DD) ou DD/MM/AAAA. Nenhuma linha foi descartada."
        )
    df["Data"] = datas
    if "Bairro" not in df:
        df["Bairro"] = pd.Series(pd.NA, index=df.index, dtype="string")
    return df


def normalizar_cadastro(df: pd.DataFrame) -> pd.DataFrame:
    validar_colunas(df, COLUNAS_CADASTRO)
    _validar_identificadores(df, ("ProCod", "ProNom"))
    resultado = df.drop_duplicates().copy()
    if resultado["ProCod"].duplicated().any():
        raise ErroDados("O cadastro contém códigos de produto com registros conflitantes.")
    return resultado


def ler_cadastro(fonte: FonteCSV) -> pd.DataFrame:
    return normalizar_cadastro(_ler_csv(fonte))
