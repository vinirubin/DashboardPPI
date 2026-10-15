from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parents[1]
PAGINAS = sorted((RAIZ / "pages").glob("*.py"))


@pytest.fixture
def app(tmp_path, vendas_csv, cadastro_csv):
    vendas = tmp_path / "vendas.csv"
    cadastro = tmp_path / "cadastro.csv"
    vendas.write_text(vendas_csv, encoding="utf-8")
    cadastro.write_text(cadastro_csv, encoding="utf-8")
    at = AppTest.from_file(str(RAIZ / "Home.py"), default_timeout=10)
    at.session_state["caminho_vendas"] = str(vendas)
    at.session_state["caminho_cadastro"] = str(cadastro)
    return at.run()


def mudar_pagina(app, prefixo):
    pagina = next(p for p in PAGINAS if p.name.startswith(prefixo))
    return app.switch_page(str(pagina.relative_to(RAIZ))).run()


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.stem)
def test_todas_paginas_com_dados(app, pagina):
    app.switch_page(str(pagina.relative_to(RAIZ))).run()
    assert not app.exception
    assert not app.error


@pytest.mark.parametrize("prefixo", ["2_", "5_", "6_"])
def test_telas_agregadas_independem_do_cadastro(app, prefixo):
    app.session_state["caminho_cadastro"] = "inexistente.csv"
    mudar_pagina(app, prefixo)
    assert not app.exception
    assert not app.error


@pytest.mark.parametrize("prefixo", ["2_", "5_"])
def test_filtro_deixa_tela_vazia_sem_nan(app, prefixo):
    vendas = Path(app.session_state["caminho_vendas"])
    texto = vendas.read_text(encoding="utf-8")
    vendas.write_text(texto.replace("0007", "99999"), encoding="utf-8")
    mudar_pagina(app, prefixo)
    assert not app.exception
    assert not app.error
    assert app.info
    assert all("nan" not in m.value.lower() and "inf" not in m.value.lower() for m in app.metric)
    app.checkbox[0].uncheck().run()
    assert not app.exception
    assert not app.error


def test_configuracao_recarrega_dados_e_da_feedback(app):
    mudar_pagina(app, "8_df_vendas.")
    assert app.session_state["df_vendas"].TotalItem.sum() == pytest.approx(47.75)
    mudar_pagina(app, "9_")
    arquivo = Path(app.session_state["caminho_vendas"])
    arquivo.write_text(
        arquivo.read_text(encoding="utf-8").replace("10.50", "110.50"), encoding="utf-8"
    )
    app.button[0].click().run()
    assert not app.exception
    assert app.success
    assert app.session_state["df_vendas_agrupado"].TotalVenda.sum() == pytest.approx(147.75)
    mudar_pagina(app, "2_")
    assert app.metric[1].value == "R$ 135,75"


def test_configuracao_invalida_preserva_dados_e_recupera(app):
    mudar_pagina(app, "8_df_vendas.")
    mudar_pagina(app, "9_")
    anterior = app.session_state["df_vendas"].TotalItem.sum()
    app.text_input[0].set_value("arquivo-inexistente.csv")
    app.button[0].click().run()
    assert not app.exception
    assert app.error
    assert app.session_state["df_vendas"].TotalItem.sum() == anterior
    app.text_input[0].set_value(app.session_state["caminho_vendas"])
    app.button[0].click().run()
    assert not app.exception
    assert not app.error
    assert app.success


def test_selecao_sem_colunas_nao_informa_todos_vendidos(app):
    mudar_pagina(app, "4_")
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert "Selecione ao menos uma coluna" in app.info[0].value


@pytest.mark.parametrize("prefixo", ["2_", "3_", "4_", "5_", "6_", "8_df_vendas.", "8_df_vendas_"])
def test_arquivo_ausente_apresenta_erro_controlado(app, prefixo):
    app.session_state["caminho_vendas"] = "ausente-confidencial.csv"
    mudar_pagina(app, prefixo)
    assert not app.exception
    assert app.error
    assert "confidencial" not in app.error[0].value


def test_paginacao_reduzida_ajusta_pagina(tmp_path):
    script = tmp_path / "paginacao.py"
    script.write_text(
        "from utils.visualizacao import mostrar_paginado\n"
        "import pandas as pd\n"
        "import streamlit as st\n"
        "mostrar_paginado(pd.DataFrame({'x':range(st.session_state['linhas'])}), 'teste')",
        encoding="utf-8",
    )
    at = AppTest.from_file(str(script), default_timeout=10)
    at.session_state["linhas"] = 250
    at.run()
    at.number_input[0].set_value(3).run()
    assert len(at.dataframe[0].value) == 50
    at.session_state["linhas"] = 10
    at.run()
    assert not at.exception
    assert at.number_input[0].value == 1
    assert len(at.dataframe[0].value) == 10


@pytest.mark.parametrize("tamanho", [0, -1, True, 1.5])
def test_paginacao_rejeita_tamanho_invalido(tamanho):
    from utils.visualizacao import mostrar_paginado

    with pytest.raises(ValueError, match="inteiro positivo"):
        mostrar_paginado(pd.DataFrame({"x": [1]}), "teste", tamanho)


def test_paginacao_vazia(tmp_path):
    script = tmp_path / "vazio.py"
    script.write_text(
        "from utils.visualizacao import mostrar_paginado\n"
        "import pandas as pd\n"
        "mostrar_paginado(pd.DataFrame(), 'vazio')",
        encoding="utf-8",
    )
    at = AppTest.from_file(str(script)).run()
    assert not at.exception
    assert at.info


def test_tela_produtos_com_volume_acima_limite_altair(app):
    vendas = Path(app.session_state["caminho_vendas"])
    cadastro = Path(app.session_state["caminho_cadastro"])
    vendas.write_text(
        "ProCod;Quantidade;TotalItem;Data;Controle;Cliente\n"
        + "".join(f"{i};1;2;2025-01-01;A;7\n" for i in range(6001)),
        encoding="utf-8",
    )
    cadastro.write_text(
        "ProCod;ProNom\n" + "".join(f"{i};Produto {i}\n" for i in range(6001)),
        encoding="utf-8",
    )
    mudar_pagina(app, "3_")
    assert not app.exception
    assert not app.error
    assert any("5000" in mensagem.value for mensagem in app.info)
    assert len(app.session_state["df_vendas"]) == 6001
    assert len(app.dataframe[1].value) == 100
