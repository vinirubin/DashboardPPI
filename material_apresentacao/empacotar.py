"""Cria uma galeria e ZIP com uma lista explícita de artefatos públicos."""

import hashlib
import html
import json
import zipfile
from pathlib import Path

from PIL import Image

PASTA = Path(__file__).resolve().parent

TITULOS = {
    "01_indicadores_sinteticos": "Interface · indicadores gerais",
    "02_detalhamento_mensal_sintetico": "Interface · detalhamento mensal",
    "03_produtos_sinteticos": "Interface · produtos vendidos",
    "04_grafico_produtos_sinteticos": "Interface · gráfico de produtos",
    "05_clientes_sinteticos": "Interface · análise de clientes",
    "06_regioes_sinteticas": "Interface · vendas por região",
    "01_evolucao_mensal": "Evolução mensal das vendas",
    "02_top_produtos": "Ranking de produtos",
    "03_recorrencia_clientes": "Recorrência dos clientes",
    "04_vendas_regiao": "Vendas por região",
    "05_vendas_dia_semana": "Vendas por dia da semana",
    "06_arquitetura_projeto": "Arquitetura do projeto",
}


def cards(arquivos: list[Path], *, vetorial: bool) -> str:
    blocos = []
    for arquivo in arquivos:
        caminho = html.escape(arquivo.relative_to(PASTA).as_posix())
        titulo = html.escape(TITULOS[arquivo.stem])
        links = f'<a href="{caminho}" download>Baixar {arquivo.suffix[1:].upper()}</a>'
        if vetorial:
            svg = html.escape(arquivo.with_suffix(".svg").relative_to(PASTA).as_posix())
            links += f'<a href="{svg}" download>Baixar SVG vetorial</a>'
        blocos.append(
            f'<article><a href="{caminho}" target="_blank"><img src="{caminho}" alt="{titulo}"></a>'
            f'<div class="card-body"><h3>{titulo}</h3><div class="links">{links}</div></div></article>'
        )
    return "\n".join(blocos)


def empacotar() -> None:
    capturas = sorted((PASTA / "capturas").glob("*.jpg"))
    graficos = sorted((PASTA / "graficos").glob("*.png"))
    vetores = sorted((PASTA / "graficos").glob("*.svg"))
    assert len(capturas) == len(graficos) == len(vetores) == 6
    for imagem in capturas + graficos:
        with Image.open(imagem) as conteudo:
            conteudo.verify()
        with Image.open(imagem) as conteudo:
            assert not conteudo.getexif(), f"EXIF inesperado: {imagem.name}"
            assert conteudo.size == ((1920, 1080) if imagem.suffix == ".png" else (1280, 720))
    for svg in vetores:
        texto = svg.read_text(encoding="utf-8")
        assert "C:\\Users" not in texto and "C:/Users" not in texto
        assert "DADOS SINTÉTICOS" in texto or "ARQUITETURA" in texto

    pagina = """<!doctype html>
<html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DashboardPPI · material para apresentação</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#10151f;color:#eef3fc;font:16px/1.6 system-ui,sans-serif}
main{max-width:1200px;margin:auto;padding:48px 28px 80px}.badge{display:inline-block;color:#2dd4bf;background:#163334;border-radius:24px;padding:6px 14px;font-size:12px;letter-spacing:1px;font-weight:700}
h1{font-size:42px;line-height:1.15;margin:24px 0 16px}h2{font-size:26px;margin:48px 0 8px}h3{margin:0 0 12px;font-size:17px}.lead{max-width:840px;color:#b5c2d6;font-size:18px}
.notice{border-left:3px solid #2dd4bf;background:#182333;padding:16px 22px;margin:24px 0}nav,.links{display:flex;gap:18px;flex-wrap:wrap}nav{margin:28px 0}a{color:#93c5fd;text-decoration:none}a:hover{text-decoration:underline}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:24px}article{background:#1b2433;border:1px solid #304058;border-radius:14px;overflow:hidden}article img{display:block;width:100%;aspect-ratio:16/9;object-fit:contain}.card-body{padding:20px}.links{font-size:14px}
footer{margin-top:50px;color:#9daec7;font-size:14px}@media(max-width:800px){.grid{grid-template-columns:1fr}h1{font-size:32px}main{padding:28px 18px}}
</style></head><body><main>
<span class="badge">APRESENTAÇÃO PÚBLICA · DADOS SINTÉTICOS</span>
<h1>DashboardPPI</h1>
<p class="lead">Capturas da interface, gráficos para slides e um diagrama de arquitetura para apresentar o projeto.</p>
<div class="notice"><strong>Todos os dados exibidos são fictícios.</strong> Produtos, clientes, regiões, números e tendências foram gerados do zero. Não são estatísticas nem registros anonimizados do conjunto comercial.</div>
<nav><a href="#interface">Capturas da interface</a><a href="#graficos">Gráficos e arquitetura</a><a href="GUIA_DE_USO.md">Guia de uso</a></nav>
<h2 id="interface">Capturas da aplicação</h2><p class="lead">As páginas originais foram executadas em uma demonstração separada com dados sintéticos. Formato JPG, 1280 × 720.</p>
<section class="grid">__CAPTURAS__</section>
<h2 id="graficos">Gráficos para slides e arquitetura</h2><p class="lead">PNG em 1920 × 1080 e SVG vetorial. Gráficos avulsos preparados para apresentação; não são capturas de telas adicionais da aplicação.</p>
<section class="grid">__GRAFICOS__</section>
<footer>Mantenha os rótulos “dados fictícios” e “dados sintéticos” visíveis ao usar as imagens. Esta galeria não utiliza serviços externos.</footer>
</main></body></html>"""
    pagina = pagina.replace("__CAPTURAS__", cards(capturas, vetorial=False))
    pagina = pagina.replace("__GRAFICOS__", cards(graficos, vetorial=True))
    (PASTA / "galeria.html").write_text(pagina, encoding="utf-8")

    arquivos = capturas + graficos + vetores + [PASTA / "galeria.html", PASTA / "GUIA_DE_USO.md"]
    manifesto = {
        "dados": "100% sintéticos, independentes do conjunto comercial",
        "conteudo": "6 capturas JPG; 5 gráficos e 1 diagrama em PNG/SVG; galeria; guia",
        "arquivos": [
            {
                "caminho": arquivo.relative_to(PASTA).as_posix(),
                "bytes": arquivo.stat().st_size,
                "sha256": hashlib.sha256(arquivo.read_bytes()).hexdigest(),
            }
            for arquivo in arquivos
        ],
    }
    (PASTA / "MANIFESTO_PUBLICO.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    arquivos.append(PASTA / "MANIFESTO_PUBLICO.json")
    destino = PASTA / "DashboardPPI_material_publico.zip"
    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as pacote:
        for arquivo in arquivos:
            pacote.write(
                arquivo, Path("DashboardPPI_material_publico") / arquivo.relative_to(PASTA)
            )
    with zipfile.ZipFile(destino) as pacote:
        assert pacote.testzip() is None
        assert all(
            Path(nome).suffix in {".jpg", ".png", ".svg", ".html", ".md", ".json"}
            for nome in pacote.namelist()
        )
    print(
        json.dumps(
            {"zip": str(destino), "arquivos": len(arquivos), "bytes": destino.stat().st_size}
        )
    )


if __name__ == "__main__":
    empacotar()
