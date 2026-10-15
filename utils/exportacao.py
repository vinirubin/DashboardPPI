"""CSV para abertura em planilhas, com neutralização de fórmulas textuais."""

import pandas as pd

PREFIXOS_FORMULA = ("=", "+", "-", "@", "\t", "\r", "\n", "＝", "＋", "－", "＠")


def _texto_seguro(valor: object) -> object:
    if isinstance(valor, str) and (
        valor.startswith(PREFIXOS_FORMULA) or valor.lstrip().startswith(PREFIXOS_FORMULA)
    ):
        return "'" + valor
    return valor


def gerar_csv_seguro(df: pd.DataFrame) -> bytes:
    resultado = df.copy()
    # Valores numéricos (incluindo devoluções negativas) continuam numéricos.
    for coluna in resultado.select_dtypes(include=["object", "string", "category"]):
        resultado[coluna] = resultado[coluna].astype(object).map(_texto_seguro)
    resultado.columns = [_texto_seguro(coluna) for coluna in resultado.columns]
    return resultado.to_csv(index=False).encode("utf-8-sig")
