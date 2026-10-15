"""Exporta gráficos de apresentação usando exclusivamente o JSON sintético."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import patches  # noqa: E402
from matplotlib.ticker import FuncFormatter, MaxNLocator  # noqa: E402

PASTA = Path(__file__).resolve().parent
SAIDA = PASTA / "graficos"
BG = "#10151f"
FG = "#eef3fc"
MUTED = "#9daec7"
BLUE = "#60a5fa"
TEAL = "#2dd4bf"
GRID = "#293547"
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 13,
        "axes.facecolor": BG,
        "figure.facecolor": BG,
        "axes.labelcolor": MUTED,
        "xtick.color": MUTED,
        "ytick.color": FG,
        "text.color": FG,
        "svg.fonttype": "none",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.spines.bottom": False,
    }
)


def br(valor: float) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def moldura(titulo: str, subtitulo: str, *, arquitetura: bool = False):
    fig = plt.figure(figsize=(12.8, 7.2), dpi=150)
    fig.text(0.055, 0.91, titulo, fontsize=26, weight="bold")
    fig.text(0.055, 0.855, subtitulo, fontsize=12, color=MUTED)
    fig.text(
        0.94,
        0.955,
        "ARQUITETURA" if arquitetura else "DADOS SINTÉTICOS",
        ha="right",
        fontsize=10,
        weight="bold",
        color=TEAL,
    )
    fig.text(0.055, 0.045, "DashboardPPI  /  Material de apresentação", color=MUTED, fontsize=10)
    fig.text(
        0.94,
        0.045,
        "Diagrama conceitual do código"
        if arquitetura
        else "Valores fictícios · sem dados comerciais",
        ha="right",
        color=MUTED,
        fontsize=10,
    )
    return fig


def salvar(fig, nome: str) -> None:
    SAIDA.mkdir(exist_ok=True)
    for formato in ("png", "svg"):
        fig.savefig(SAIDA / f"{nome}.{formato}", dpi=150, facecolor=BG)
    plt.close(fig)


def eixo(fig, *, esquerda=0.14, direita=0.94):
    ax = fig.add_axes((esquerda, 0.20, direita - esquerda, 0.56))
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.tick_params(length=0, pad=10)
    return ax


def gerar() -> None:
    dados = json.loads((PASTA / "dados_sinteticos.json").read_text(encoding="utf-8"))
    assert dados["proveniencia"].startswith("Dados 100% sintéticos")

    fig = moldura(
        "Evolução mensal das vendas", "Exemplo de análise temporal · cenário fictício de 2025"
    )
    ax = eixo(fig, esquerda=0.12)
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    valores = [linha["TotalVenda"] for linha in dados["mensal"]]
    ax.plot(range(12), valores, color=BLUE, linewidth=3.5, marker="o", markersize=7)
    ax.fill_between(range(12), valores, color=BLUE, alpha=0.12)
    ax.set_xticks(range(12), meses)
    ax.set_ylim(0, max(valores) * 1.24)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"R$ {x / 1000:.0f} mil"))
    for i, valor in enumerate(valores):
        ax.annotate(
            br(valor),
            (i, valor),
            xytext=(0, 13),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )
    salvar(fig, "01_evolucao_mensal")

    fig = moldura(
        "Produtos com maior valor vendido",
        "Ranking demonstrativo · produtos e valores inteiramente fictícios",
    )
    ax = eixo(fig, esquerda=0.17)
    produtos = sorted(dados["produtos"][:10], key=lambda p: p["TotalItem"])
    nomes = [p["Produto"] for p in produtos]
    valores = [p["TotalItem"] for p in produtos]
    ax.grid(False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.barh(nomes, valores, height=0.62, color=["#3b82f6"] * 9 + [TEAL])
    ax.set_xlim(0, max(valores) * 1.28)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 5, 10]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"R$ {x / 1000:.0f} mil"))
    for i, valor in enumerate(valores):
        ax.text(valor + max(valores) * 0.02, i, f"R$ {br(valor)}", va="center", fontsize=11)
    salvar(fig, "02_top_produtos")

    fig = moldura(
        "Recorrência dos clientes",
        "Clientes que compram novamente · exemplo com identidades geradas",
    )
    retornaram = dados["clientes_retornaram"]
    uma_compra = dados["clientes"] - retornaram
    ax = fig.add_axes((0.07, 0.17, 0.47, 0.61))
    ax.pie(
        [retornaram, uma_compra],
        colors=[BLUE, "#334155"],
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.23, "edgecolor": BG, "linewidth": 3},
    )
    ax.text(0, 0.05, str(dados["clientes"]), ha="center", va="center", fontsize=42, weight="bold")
    ax.text(0, -0.22, "clientes fictícios", ha="center", fontsize=14, color=MUTED)
    fig.text(
        0.60,
        0.64,
        f"{retornaram / dados['clientes']:.1%}".replace(".", ","),
        fontsize=44,
        color=BLUE,
        weight="bold",
    )
    fig.text(0.60, 0.56, "Taxa de retorno", fontsize=17)
    fig.text(0.60, 0.43, f"{retornaram} com mais de uma compra", fontsize=16)
    fig.text(0.60, 0.35, f"{uma_compra} com uma única compra", fontsize=16, color=MUTED)
    salvar(fig, "03_recorrencia_clientes")

    fig = moldura(
        "Vendas por região",
        "Comparação geográfica demonstrativa · regiões sem correspondência real",
    )
    ax = eixo(fig, esquerda=0.17)
    regioes = sorted(dados["regioes"], key=lambda p: p["Vendas"])
    valores = [p["Vendas"] for p in regioes]
    ax.grid(False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.barh([p["Bairro"] for p in regioes], valores, height=0.58, color=TEAL)
    ax.set_xlim(0, max(valores) * 1.20)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
    ax.set_xlabel("Número de vendas fictícias", labelpad=14)
    for i, valor in enumerate(valores):
        ax.text(valor + 2, i, str(valor), va="center", fontsize=16, weight="bold")
    salvar(fig, "04_vendas_regiao")

    fig = moldura(
        "Vendas por dia da semana",
        "Distribuição temporal · exemplo independente do conjunto comercial",
    )
    ax = eixo(fig, esquerda=0.12)
    valores = [p["TotalVenda"] for p in dados["dias_semana"]]
    ax.bar(["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"], valores, color=BLUE, width=0.58)
    ax.set_ylim(0, max(valores) * 1.23)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"R$ {x / 1000:.0f} mil"))
    for i, valor in enumerate(valores):
        ax.text(i, valor + max(valores) * 0.04, f"R$ {br(valor)}", ha="center", fontsize=11)
    salvar(fig, "05_vendas_dia_semana")

    fig = moldura(
        "Como o projeto organiza a análise",
        "Fluxo conceitual dos dados e principais módulos",
        arquitetura=True,
    )
    ax = fig.add_axes((0.045, 0.15, 0.91, 0.63))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    caixas = [
        (0.015, 0.59, "Arquivos CSV", "Vendas e cadastro"),
        (0.27, 0.59, "Validação", "dados.py"),
        (0.525, 0.59, "Transformações", "processamento.py"),
        (0.78, 0.59, "Estado da sessão", "sessao.py"),
        (0.78, 0.12, "Indicadores", "analise.py"),
        (0.525, 0.12, "Cache de cálculos", "cache.py"),
        (0.27, 0.12, "Interface", "Home.py + pages/"),
        (0.015, 0.12, "Tabelas e CSV", "visualizacao.py\nexportacao.py"),
    ]
    largura, altura = 0.205, 0.25
    for x, y, titulo, modulo in caixas:
        ax.add_patch(
            patches.FancyBboxPatch(
                (x, y),
                largura,
                altura,
                boxstyle="round,pad=0.012,rounding_size=0.02",
                facecolor="#1b273a",
                edgecolor="#3b5579",
                linewidth=1.3,
            )
        )
        ax.text(
            x + largura / 2,
            y + altura * 0.67,
            titulo,
            ha="center",
            va="center",
            fontsize=12,
            weight="bold",
        )
        ax.text(
            x + largura / 2,
            y + altura * 0.32,
            modulo,
            ha="center",
            va="center",
            fontsize=10,
            color=MUTED,
        )
    for i in range(7):
        x1, y1, *_ = caixas[i]
        x2, y2, *_ = caixas[i + 1]
        if i < 3:
            inicio, fim = (x1 + largura + 0.006, y1 + altura / 2), (x2 - 0.015, y2 + altura / 2)
        elif i == 3:
            inicio, fim = (x1 + largura / 2, y1 - 0.02), (x2 + largura / 2, y2 + altura + 0.02)
        else:
            inicio, fim = (x1 - 0.018, y1 + altura / 2), (x2 + largura + 0.014, y2 + altura / 2)
        ax.annotate(
            "",
            xy=fim,
            xytext=inicio,
            arrowprops={"arrowstyle": "-|>", "color": BLUE, "lw": 2, "mutation_scale": 14},
        )
    salvar(fig, "06_arquitetura_projeto")

    print(f"{len(list(SAIDA.glob('*.png')))} gráficos PNG e SVG gerados em {SAIDA}")


if __name__ == "__main__":
    gerar()
