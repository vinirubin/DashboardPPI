from io import StringIO

import pytest

from utils.dados import ler_cadastro, ler_vendas
from utils.processamento import adicionar_periodos, agrupar_vendas_por_controle


@pytest.fixture
def vendas_csv():
    return (
        "ProCod;Quantidade;TotalItem;Data;Controle;Cliente;Bairro\n"
        "001;2;10.50;31/12/2024;A;0007;Centro\n"
        "002;3;20.25;31/12/2024;A;0007;Centro\n"
        "001;1;5.00;2025-01-01;B;0007;Centro\n"
        "004;4;12.00;2026-01-01;C;99999;\n"
    )


@pytest.fixture
def cadastro_csv():
    return "ProCod;ProNom;Categoria\n001;Arroz;Alimento\n002;Arroz;Alimento\n003;Feijão;Alimento\n"


@pytest.fixture
def vendas(vendas_csv):
    return adicionar_periodos(ler_vendas(StringIO(vendas_csv)))


@pytest.fixture
def cadastro(cadastro_csv):
    return ler_cadastro(StringIO(cadastro_csv))


@pytest.fixture
def agrupado(vendas):
    return agrupar_vendas_por_controle(vendas)
