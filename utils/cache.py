"""Cache limitado, invalidado pelo conteúdo integral de cada DataFrame."""

from collections.abc import Callable
from hashlib import sha256
from typing import TypeVar

import pandas as pd
import streamlit as st

Funcao = TypeVar("Funcao", bound=Callable)


def assinatura_dataframe(df: pd.DataFrame) -> str:
    assinatura = sha256()
    assinatura.update(repr((df.shape, tuple(df.columns), tuple(map(str, df.dtypes)))).encode())
    # A conversão para bytes também evita a amostragem de arrays pelo Streamlit.
    assinatura.update(pd.util.hash_pandas_object(df, index=True).to_numpy().tobytes())
    return assinatura.hexdigest()


def cache_calculo(funcao: Funcao, *, max_entries: int = 8, ttl: int = 300) -> Funcao:
    return st.cache_data(
        max_entries=max_entries, ttl=ttl, hash_funcs={pd.DataFrame: assinatura_dataframe}
    )(funcao)
