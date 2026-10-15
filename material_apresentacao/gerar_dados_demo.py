"""Gera dados fictícios sem ler, copiar ou transformar o conjunto comercial."""

import json
import random
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from utils.analise import (  # noqa: E402
    agrupar_tabelas_temporais,
    calcular_metricas_clientes,
    calcular_vendas_por_localizacao,
    filtrar_clientes_identificados,
    preparar_produtos,
)
from utils.processamento import adicionar_periodos, agrupar_vendas_por_controle  # noqa: E402

PASTA = Path(__file__).resolve().parent


def gerar_dados() -> tuple[pd.DataFrame, pd.DataFrame]:
    aleatorio = random.Random(731)
    cadastro = pd.DataFrame(
        {
            "ProCod": [f"PROD-DEMO-{i:03}" for i in range(1, 21)],
            "ProNom": [f"Produto {chr(64 + i)}" for i in range(1, 21)],
            "Categoria": ["Categoria ilustrativa"] * 20,
        }
    )
    precos = [7.5, 12.9, 18.5, 24.9, 9.9, 32.5, 45.0, 6.9, 16.5, 22.0, 28.9, 39.9]
    itens = []
    for mes in range(1, 13):
        numero_vendas = 20 + mes * 2 + aleatorio.randint(0, 9)
        for numero in range(numero_vendas):
            data = pd.Timestamp(2025, mes, aleatorio.randint(1, 28))
            cliente = f"CLIENTE-DEMO-{aleatorio.randint(1, 80):03}"
            bairro = f"Região {aleatorio.choice('ABCDE')}"
            controle = f"VENDA-DEMO-{mes:02}-{numero + 1:03}"
            produtos = aleatorio.sample(range(12), aleatorio.randint(1, 5))
            for produto in produtos:
                quantidade = aleatorio.randint(1, 5)
                itens.append(
                    {
                        "Data": data,
                        "Controle": controle,
                        "Cliente": cliente,
                        "Bairro": bairro,
                        "ProCod": cadastro.iloc[produto].ProCod,
                        "Quantidade": quantidade,
                        "TotalItem": round(quantidade * precos[produto], 2),
                    }
                )
    return adicionar_periodos(pd.DataFrame(itens)), cadastro


def salvar_material() -> None:
    vendas, cadastro = gerar_dados()
    agrupado = agrupar_vendas_por_controle(vendas)
    tabelas = agrupar_tabelas_temporais(agrupado)
    produtos = preparar_produtos(vendas, cadastro)
    clientes, retornaram, perfis = calcular_metricas_clientes(
        filtrar_clientes_identificados(agrupado)
    )
    bairros = calcular_vendas_por_localizacao(agrupado, "Bairro")
    resumo = {
        "proveniencia": "Dados 100% sintéticos gerados com semente fixa 731; nenhum CSV real lido.",
        "ano_ficticio": 2025,
        "clientes": clientes,
        "clientes_retornaram": retornaram,
        "vendas": len(agrupado),
        "valor_total": round(float(agrupado.TotalVenda.sum()), 2),
        "produtos_cadastrados": len(cadastro),
        "produtos_vendidos": len(produtos),
        "mensal": tabelas[3].to_dict(orient="records"),
        "dias_semana": tabelas[5].astype({"DiaSemana": "string"}).to_dict(orient="records"),
        "produtos": produtos.to_dict(orient="records"),
        "regioes": bairros.to_dict(orient="records"),
        "perfil_clientes": perfis.to_dict(orient="records"),
    }
    PASTA.mkdir(exist_ok=True)
    (PASTA / "dados_sinteticos.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"tipo": "sintetico", "vendas": len(agrupado), "clientes": clientes}))


if __name__ == "__main__":
    salvar_material()
