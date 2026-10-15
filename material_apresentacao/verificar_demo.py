"""Verifica a demonstração proibindo qualquer leitura de CSV durante a execução."""

import json
from pathlib import Path
from unittest.mock import patch

from gerar_dados_demo import gerar_dados
from streamlit.testing.v1 import AppTest

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parent


def verificar() -> None:
    with patch("pandas.read_csv", side_effect=AssertionError("Leitura de CSV proibida no demo")):
        vendas, cadastro = gerar_dados()
        novamente, _ = gerar_dados()
        assert vendas.equals(novamente)
        assert vendas.ProCod.str.startswith("PROD-DEMO-").all()
        assert vendas.Cliente.str.startswith("CLIENTE-DEMO-").all()
        assert cadastro.ProNom.str.fullmatch(r"Produto [A-T]").all()
        assert vendas.Bairro.str.fullmatch(r"Região [A-E]").all()
        assert vendas.Data.dt.year.eq(2025).all()
        app = AppTest.from_file(str(PASTA / "Demo.py"), default_timeout=20).run()
        assert not app.exception and not app.error
        paginas = []
        for prefixo in ("2_", "3_", "4_", "5_", "6_"):
            arquivo = next((RAIZ / "pages").glob(f"{prefixo}*.py"))
            app.switch_page(str(Path("..") / "pages" / arquivo.name)).run()
            assert not app.exception, arquivo.name
            assert not app.error, arquivo.name
            assert app.session_state["df_vendas"].Cliente.str.startswith("CLIENTE-DEMO-").all()
            paginas.append(arquivo.name)
    resultado = {
        "status": "aprovado",
        "dados_sinteticos": True,
        "geracao_deterministica": True,
        "leitura_csv_bloqueada_durante_verificacao": True,
        "paginas_verificadas": paginas,
    }
    (PASTA / "verificacao_demo.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(resultado, ensure_ascii=True))


if __name__ == "__main__":
    verificar()
