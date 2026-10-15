from types import SimpleNamespace

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from utils import sessao
from utils.caminho import RAIZ_PROJETO, caminho_valido, resolver_caminho
from utils.dados import ErroDados


@pytest.fixture
def estado(monkeypatch):
    erros = []

    def parar():
        raise RuntimeError("Execução interrompida")

    fake = SimpleNamespace(session_state={}, error=erros.append, stop=parar)
    monkeypatch.setattr(sessao, "st", fake)
    return fake.session_state, erros


def test_inicializacao_preserva_caminhos_existentes(estado):
    state, _ = estado
    state["caminho_vendas"] = "personalizado.csv"
    sessao.inicializar_app()
    sessao.inicializar_app()
    assert state["caminho_vendas"] == "personalizado.csv"
    assert state["caminho_cadastro"] == "dados/prodMercado.csv"


def test_recarga_atomica_e_mesmo_caminho(estado, tmp_path, vendas_csv, cadastro_csv):
    state, erros = estado
    vendas = tmp_path / "vendas.csv"
    cadastro = tmp_path / "cadastro.csv"
    vendas.write_text(vendas_csv, encoding="utf-8")
    cadastro.write_text(cadastro_csv, encoding="utf-8")
    state.update(df_vendas=pd.DataFrame({"antigo": [1]}), pagina_df_vendas=5, preferencia="manter")
    assert sessao.salvar_caminhos(str(vendas), str(cadastro))
    assert state["df_vendas_agrupado"].TotalVenda.sum() == pytest.approx(47.75)
    assert "pagina_df_vendas" not in state
    assert state["preferencia"] == "manter"
    vendas.write_text(vendas_csv.replace("10.50", "100.50"), encoding="utf-8")
    assert sessao.salvar_caminhos(str(vendas), str(cadastro))
    assert state["df_vendas"].TotalItem.sum() == pytest.approx(137.75)
    assert not erros


@pytest.mark.parametrize("falha", ["vendas", "cadastro", "controle", "inexistente"])
def test_falha_preserva_todo_estado(estado, tmp_path, vendas_csv, cadastro_csv, falha):
    state, erros = estado
    vendas = tmp_path / "vendas.csv"
    cadastro = tmp_path / "cadastro.csv"
    vendas.write_text(vendas_csv, encoding="utf-8")
    cadastro.write_text(cadastro_csv, encoding="utf-8")
    assert sessao.salvar_caminhos(str(vendas), str(cadastro))
    anterior = dict(state)
    if falha == "vendas":
        vendas.write_text("outra\n1\n", encoding="utf-8")
    elif falha == "cadastro":
        cadastro.write_text(cadastro_csv + "001;Conflito;Outro\n", encoding="utf-8")
    elif falha == "controle":
        vendas.write_text(
            vendas_csv.replace("002;3;20.25;31/12/2024;A;0007", "002;3;20.25;31/12/2024;A;outro"),
            encoding="utf-8",
        )
    else:
        vendas = tmp_path / "inexistente.csv"
    assert not sessao.salvar_caminhos(str(vendas), str(cadastro))
    assert erros
    assert state.keys() == anterior.keys()
    for chave in anterior:
        assert state[chave] is anterior[chave]


def test_carregador_nao_sobrescreve_dataframe_com_none(estado):
    state, erros = estado
    state["df"] = pd.DataFrame({"original": [1]})
    assert not sessao.carregar_arquivo_na_sessao("df", "qualquer", lambda _: None, forcar=True)
    assert state["df"].original.tolist() == [1]
    assert erros
    assert sessao.carregar_arquivo_na_sessao("df", None, lambda _: None)


def test_carregador_valida_cache_e_erros(estado):
    state, erros = estado
    state["df"] = None
    assert not sessao.df_em_cache("df")
    assert not sessao.carregar_arquivo_na_sessao("df", None, lambda _: None)
    assert not sessao.carregar_arquivo_na_sessao("df", "", lambda _: None)

    def falhar(_):
        raise ErroDados("Erro esperado")

    assert not sessao.carregar_arquivo_na_sessao("df", "origem", falhar)
    assert erros[-1] == "Erro esperado"
    assert sessao.carregar_arquivo_na_sessao("df", "origem", lambda _: pd.DataFrame({"x": [1]}))
    assert sessao.df_em_cache("df")


def test_carregador_generico_sanitiza_falha_de_io(estado):
    _, erros = estado

    def falhar(_):
        raise OSError("caminho-confidencial")

    assert not sessao.carregar_arquivo_na_sessao("df", "origem", falhar)
    assert "confidencial" not in erros[-1]


def test_validar_df_recupera_invalido_e_retorna_copia(estado):
    state, _ = estado
    state["df"] = None

    def carregar():
        state["df"] = pd.DataFrame({"valor": [10]})

    copia = sessao.validar_df("df", carregar)
    assert_frame_equal(copia, state["df"])
    copia.loc[0, "valor"] = 99
    assert state["df"].valor.iloc[0] == 10
    with pytest.raises(RuntimeError, match="interrompida"):
        sessao.validar_df("ausente", lambda: None)


def test_caminhos_relativos_independentes_do_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert resolver_caminho("Home.py") == RAIZ_PROJETO / "Home.py"
    assert caminho_valido("Home.py")
    assert caminho_valido(RAIZ_PROJETO / "Home.py")
    assert not caminho_valido(None)
    assert not caminho_valido(123)
    assert not caminho_valido("")
    assert not caminho_valido("arquivo-inexistente")
    assert not caminho_valido("\x00")
