# DashboardPPI — material para apresentação

Este material foi preparado para mostrar o projeto sem divulgar o conjunto
comercial. Os números, séries, produtos, clientes e regiões foram gerados do
zero, com semente fixa. Não são dados reais anonimizados nem estatísticas
derivadas dos arquivos comerciais.

## Conteúdo do pacote público

- **6 capturas JPG** das páginas reais do projeto executadas com dados fictícios.
- **5 gráficos de demonstração**, em PNG 1920 × 1080 e SVG vetorial.
- **1 diagrama da arquitetura**, também em PNG 1920 × 1080 e SVG.
- Galeria HTML local para visualizar e escolher as imagens.

Os gráficos avulsos foram preparados para slides usando os resultados das
funções de análise do projeto. Eles complementam as capturas da interface;
não representam telas adicionais implementadas no dashboard.

## Sugestão de sequência para apresentação

1. `graficos/06_arquitetura_projeto.png`: explique a organização do código.
2. `capturas/01_indicadores_sinteticos.jpg`: apresente a interface e os KPIs.
3. `graficos/01_evolucao_mensal.png`: mostre a análise temporal.
4. `capturas/04_grafico_produtos_sinteticos.jpg`: mostre o gráfico da aplicação.
5. `graficos/02_top_produtos.png`: use o ranking em um slide dedicado.
6. `capturas/05_clientes_sinteticos.jpg` ou o gráfico de recorrência: apresente clientes.
7. `capturas/06_regioes_sinteticas.jpg` ou o gráfico regional: apresente a localização.

Use PNG em PowerPoint, Google Slides e documentos; use SVG para ampliar ou
editar os elementos vetoriais. As capturas JPG preservam a aparência da interface.

Mantenha os avisos **DADOS FICTÍCIOS / DADOS SINTÉTICOS** visíveis e não apresente
os números como resultados do conjunto real. O diagrama de arquitetura descreve
o código e não contém informações do conjunto de dados.

## Demonstração ao vivo

A aplicação de demonstração usa a porta 8502. Ela executa as páginas originais
com dados sintéticos em uma sessão separada. Não há tela de configuração de
arquivos nesse modo.

Para iniciar a partir da raiz do projeto:

```powershell
.\.venv\Scripts\python -m streamlit run material_apresentacao/Demo.py --server.address=127.0.0.1 --server.port=8502
```

`gerar_dados_demo.py`, `gerar_graficos.py`, `Demo.py` e o JSON de exemplo ficam
na pasta de trabalho para reprodução. O pacote ZIP de entrega contém apenas as
imagens, a galeria e este guia. Não inclui CSVs, relatórios reais nem caminhos pessoais.
