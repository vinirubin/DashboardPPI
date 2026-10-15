"""Ciclo de vida dos dados por sessão e apresentação dos erros esperados."""

from collections.abc import Callable

import pandas as pd
import streamlit as st

from utils.caminho import caminho_valido
from utils.constantes import CAMINHO_PADRAO_CADASTRO, CAMINHO_PADRAO_VENDAS
from utils.dados import ErroDados, FonteCSV, ler_cadastro, ler_vendas


def inicializar_app() -> None:
    st.session_state.setdefault("caminho_vendas", CAMINHO_PADRAO_VENDAS)
    st.session_state.setdefault("caminho_cadastro", CAMINHO_PADRAO_CADASTRO)
    st.session_state["inicializado"] = True


def invalidar_derivados() -> None:
    st.session_state.pop("df_vendas_agrupado", None)
    for chave in list(st.session_state):
        if chave.startswith("pagina_"):
            del st.session_state[chave]


def carregar_arquivo_na_sessao(
    nome_chave: str,
    caminho: FonteCSV | None,
    func_carregamento: Callable[[FonteCSV], pd.DataFrame],
    *,
    forcar: bool = False,
) -> bool:
    if not forcar and df_em_cache(nome_chave):
        return True
    if caminho is None or (isinstance(caminho, str) and not caminho.strip()):
        st.error("Configure os arquivos na página 'Carregar Arquivos'.")
        return False
    try:
        df = func_carregamento(caminho)
        if not isinstance(df, pd.DataFrame) or df.empty:
            raise ErroDados("O carregador não retornou uma tabela com registros.")
    except ErroDados as exc:
        st.error(str(exc))
        return False
    except (OSError, UnicodeError, pd.errors.ParserError):
        st.error("Não foi possível ler o CSV. Verifique acesso, UTF-8 e separador ';'.")
        return False
    st.session_state[nome_chave] = df
    return True


def df_em_cache(nome_df: str) -> bool:
    df = st.session_state.get(nome_df)
    return isinstance(df, pd.DataFrame) and not df.empty


def salvar_caminhos(
    caminho_vendas: str = CAMINHO_PADRAO_VENDAS,
    caminho_cadastro: str = CAMINHO_PADRAO_CADASTRO,
) -> bool:
    from utils.processamento import adicionar_periodos, agrupar_vendas_por_controle

    if not caminho_valido(caminho_vendas) or not caminho_valido(caminho_cadastro):
        st.error("Arquivo não encontrado. Verifique os dois caminhos informados.")
        return False
    try:
        vendas = adicionar_periodos(ler_vendas(caminho_vendas))
        cadastro = ler_cadastro(caminho_cadastro)
        agrupado = agrupar_vendas_por_controle(vendas)
    except ErroDados as exc:
        st.error(str(exc))
        return False
    # Publicação somente após ambos os CSVs e suas relações serem validados.
    invalidar_derivados()
    st.session_state.update(
        caminho_vendas=caminho_vendas,
        caminho_cadastro=caminho_cadastro,
        df_vendas=vendas,
        df_cadastro=cadastro,
        df_vendas_agrupado=agrupado,
    )
    return True


def validar_df(nome: str, carregador: Callable[[], object]) -> pd.DataFrame:
    if not df_em_cache(nome):
        carregador()
    df = st.session_state.get(nome)
    if not isinstance(df, pd.DataFrame) or df.empty:
        st.error(f"A tabela '{nome}' não está disponível ou está vazia.")
        st.stop()
    # Contrato histórico: consumidor pode formatar sem alterar a sessão.
    return df.copy()
