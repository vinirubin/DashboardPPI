from decimal import Decimal

import altair as alt
import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from utils.analise import (
    MAX_LINHAS_GRAFICO,
    PERIODOS,
    agrupar_tabelas_temporais,
    calcular_metricas_clientes,
    calcular_vendas_por_localizacao,
    detalhar_giro_vendas,
    dividir_seguro,
    filtrar_clientes_identificados,
    limitar_grafico_giro,
    obter_produtos_nao_vendidos,
    preparar_produtos,
)
from utils.dados import ErroDados
from utils.moeda import formatar_moeda_brasileira
from utils.processamento import adicionar_nomes_produtos, agrupar_vendas_por_controle


def test_controles_preservam_totais_linhas_e_unidades(agrupado):
    assert len(agrupado) == 3
    assert agrupado.TotalVenda.sum() == pytest.approx(47.75)
    venda_a = agrupado.loc[agrupado.Controle.eq("A")].iloc[0]
    assert venda_a.QuantidadeItens == 2
    assert venda_a.QuantidadeUnidades == 5


def test_controle_ambiguo_no_mesmo_dia_nao_e_silenciado(vendas):
    vendas.loc[1, "Cliente"] = "outro"
    with pytest.raises(ErroDados, match="controles"):
        agrupar_vendas_por_controle(vendas)


def test_controle_reutilizado_em_outro_dia_e_outra_venda(vendas):
    vendas.loc[1, "Data"] = pd.Timestamp("2025-02-01")
    vendas.loc[1, "Cliente"] = "outro"
    agrupado = agrupar_vendas_por_controle(vendas)
    assert len(agrupado) == 4
    assert agrupado.loc[agrupado.Controle.eq("A"), "DataVenda"].nunique() == 2
    assert agrupado.TotalVenda.sum() == pytest.approx(vendas.TotalItem.sum())
    bairros = calcular_vendas_por_localizacao(agrupado, "Bairro")
    assert bairros.Vendas.sum() == 3


def test_horarios_diferentes_do_mesmo_dia_permanecem_na_mesma_venda(vendas):
    vendas.loc[1, "Data"] = pd.Timestamp("2024-12-31 04:00:00")
    agrupado = agrupar_vendas_por_controle(vendas)
    assert len(agrupado) == 3
    assert agrupado.loc[agrupado.Controle.eq("A"), "Data"].iloc[0] == vendas.Data.iloc[0]


def test_periodos_nao_misturam_anos_e_semana_cruza_ano(agrupado):
    assert agrupado.Semestre.nunique() == 3
    assert agrupado.SemanaInicioDt.iloc[0] == agrupado.SemanaInicioDt.iloc[1]
    tabelas = agrupar_tabelas_temporais(agrupado)
    for tabela in tabelas:
        assert tabela.TotalVenda.sum() == pytest.approx(47.75)
    assert len(tabelas[1]) == 3
    assert tabelas[4].iloc[0].Meses == "2024-12 / 2025-01"
    assert tabelas[5].DiaSemana.astype(str).tolist() == [
        "terça-feira",
        "quarta-feira",
        "quinta-feira",
    ]


def test_metricas_cliente_e_retornos(agrupado):
    total, retornaram, clientes = calcular_metricas_clientes(
        filtrar_clientes_identificados(agrupado)
    )
    assert (total, retornaram) == (1, 1)
    assert clientes.iloc[0].num_compras == 2
    assert clientes.iloc[0].num_retornos == 1
    assert clientes.iloc[0].ticket_medio == pytest.approx(17.875)
    assert clientes.iloc[0].unidades_totais == 6


def test_filtro_vazio_e_cliente_ausente(agrupado):
    vazio = filtrar_clientes_identificados(agrupado.loc[agrupado.Cliente.eq("99999")])
    assert calcular_metricas_clientes(vazio)[:2] == (0, 0)
    assert dividir_seguro(0, 0) == 0
    assert all(tabela.empty for tabela in agrupar_tabelas_temporais(vazio))
    sem_cliente = agrupado.copy()
    sem_cliente["Cliente"] = pd.NA
    assert agrupar_tabelas_temporais(sem_cliente)[0].MediaPorCliente.eq(0).all()


def test_identificador_sentinela_numerico_e_texto():
    df = pd.DataFrame({"Cliente": [99999, "99999", "7", None]})
    assert filtrar_clientes_identificados(df).Cliente.tolist() == ["7"]


def test_merge_duplicado_preserva_valor_e_produto_desconhecido(vendas, cadastro):
    duplicado = pd.concat([cadastro, cadastro.iloc[[0]]])
    df = preparar_produtos(vendas, duplicado)
    assert df.TotalItem.sum() == pytest.approx(47.75)
    assert len(df) == 3
    assert "Produto sem cadastro (004)" in df.Produto.tolist()
    original = vendas.copy(deep=True)
    adicionar_nomes_produtos(vendas, cadastro)
    assert_frame_equal(vendas, original)


@pytest.mark.parametrize("periodo", list(PERIODOS))
def test_giro_preserva_identidade_e_quantidades(vendas, cadastro, periodo):
    giro = detalhar_giro_vendas(vendas, cadastro, periodo)
    assert giro.Quantidade.sum() == 10
    assert set(giro.ProCod) == {"001", "002", "004"}
    assert giro.RotuloProduto.nunique() == 3
    if periodo == "Semana":
        assert giro.Periodo.iloc[0] == vendas.SemanaInicioDt.iloc[0]
    if periodo == "Dia da Semana":
        assert giro.Periodo.astype(str).str.contains("-feira").all()


def test_giro_pode_derivar_periodo(vendas, cadastro):
    assert_frame_equal(
        detalhar_giro_vendas(vendas.drop(columns="Semestre"), cadastro, "Semestre"),
        detalhar_giro_vendas(vendas, cadastro, "Semestre"),
    )
    with pytest.raises(ValueError, match="Período"):
        detalhar_giro_vendas(vendas, cadastro, "invalido")


def test_nao_vendidos_e_bairro(vendas, cadastro, agrupado):
    assert obter_produtos_nao_vendidos(vendas, cadastro).ProCod.tolist() == ["003"]
    bairro = calcular_vendas_por_localizacao(agrupado, "Bairro")
    assert bairro.Vendas.sum() == 2
    assert bairro.ValorTotal.sum() == pytest.approx(35.75)
    assert calcular_vendas_por_localizacao(agrupado, "ausente").empty


def test_grafico_grande_serializa_sem_perder_tabela():
    df = pd.DataFrame({"Produto": [f"P{i}" for i in range(6000)], "Quantidade": range(6000)})
    grafico = limitar_grafico_giro(df)
    assert len(df) == 6000
    assert len(grafico) == MAX_LINHAS_GRAFICO
    assert grafico.Quantidade.max() == 5999
    assert alt.Chart(grafico).mark_bar().encode(x="Quantidade:Q", y="Produto:N").to_dict()
    assert len(limitar_grafico_giro(df.head(2))) == 2


@pytest.mark.parametrize(
    "valor,esperado",
    [
        (np.int64(100), "R$ 100,00"),
        (np.float64(1234.5), "R$ 1.234,50"),
        (Decimal("12.34"), "R$ 12,34"),
        (-10.5, "R$ -10,50"),
        (None, "R$ 0,00"),
        (pd.NA, "R$ 0,00"),
        (True, "R$ 0,00"),
        (float("nan"), "R$ 0,00"),
        (float("inf"), "R$ 0,00"),
        ("100", "R$ 0,00"),
        (10**1000, "R$ 0,00"),
    ],
)
def test_moeda(valor, esperado):
    assert formatar_moeda_brasileira(valor) == esperado
