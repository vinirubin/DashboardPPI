# DashboardPPI

Dashboard local de análise de vendas com Streamlit, pandas e Altair. Inclui
indicadores temporais, produtos vendidos e não vendidos, perfil de clientes,
local de entrega, inspeção paginada e exportação CSV.

## Instalação e execução

Use Python 3.11 a 3.13. A validação local foi realizada em Python 3.13.2.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt -c constraints-tested.txt
.\.venv\Scripts\python -m streamlit run Home.py --server.address=127.0.0.1
```

Em Linux/macOS, substitua `.\.venv\Scripts\python` por `.venv/bin/python`.
O arquivo de constraints registra as versões diretas validadas; não é um lock
completo de dependências transitivas. As faixas em requirements permitem evolução
compatível; atualizações devem passar pelos testes antes de alterar as constraints.

Os dados comerciais não são distribuídos. Coloque os arquivos em:

```text
dados/NotasFW_ProdInfo.csv
dados/prodMercado.csv
```

Ou abra **Carregar Arquivos** pela navegação lateral. Caminhos relativos são
resolvidos a partir da raiz do projeto, mesmo quando a aplicação inicia em outro
diretório. Os caminhos se referem ao computador que executa o servidor, não ao
computador de um visitante remoto. O aplicativo pressupõe execução local ou em
ambiente de confiança; autenticação e autorização de acesso não estão implementadas.

**Salvar Caminhos** valida e recarrega ambos os CSVs, inclusive quando os caminhos
permanecem iguais. Dados e tabelas derivadas são substituídos apenas se a operação
inteira terminar com sucesso. Uma falha preserva o conjunto anterior da sessão.
Alterações externas nos CSVs exigem uma nova recarga explícita.

## Contrato dos CSVs

- UTF-8, com ou sem BOM; separador `;`.
- Números finitos com ponto decimal, sem separador de milhares. Valores negativos
  são preservados para permitir devoluções/ajustes.
- Datas `AAAA-MM-DD` ou `DD/MM/AAAA`; horário local opcional ` HH:MM[:SS[.fração]]`
  ou `THH:MM[:SS[.fração]]`. Fusos horários não são aceitos.
- Identificadores são texto: `001` e `1` são códigos diferentes. Use o mesmo padrão
  em vendas e cadastro; zeros à esquerda são preservados.
- Cabeçalhos e células textuais têm espaços externos removidos. Células vazias
  tornam-se nulas; os textos literais `NA` e `N/A` são preservados.
- Arquivos vazios, colunas obrigatórias ausentes/duplicadas, identificadores de
  produtos/controles vazios, números ou datas inválidos são recusados. Não há
  descarte silencioso de linhas.

Vendas:

| Coluna | Contrato |
|---|---|
| `ProCod` | Código do produto, obrigatório e não vazio |
| `Quantidade` | Quantidade numérica, obrigatória |
| `TotalItem` | Valor numérico do item, obrigatório |
| `Data` | Data válida, obrigatória |
| `Controle` | Identificador da venda, obrigatório e não vazio |
| `Cliente` | Coluna obrigatória; célula vazia representa cliente desconhecido |
| `Bairro` | Opcional; ausência não impede as outras análises |

Cada venda é identificada pela combinação **DataVenda + Controle**, sendo DataVenda
a data sem horário. O sistema de origem reutiliza controles em dias diferentes.
Um mesmo controle no mesmo dia deve pertencer a um único cliente; conflitos são
recusados. A data/hora da venda é o menor horário de seus itens.

Cadastro:

| Coluna | Contrato |
|---|---|
| `ProCod` | Código único e não vazio |
| `ProNom` | Nome não vazio |

Colunas adicionais do cadastro são mantidas como texto para inspeção. Linhas
exatamente iguais são deduplicadas. Um código com registros conflitantes é
recusado. Produtos sem correspondência permanecem nas vendas com o rótulo
`Produto sem cadastro (código)`. Produtos homônimos mantêm identidades separadas.

Exemplo mínimo de vendas:

```csv
ProCod;Quantidade;TotalItem;Data;Controle;Cliente;Bairro
001;2;19.90;2025-01-03;V001;0007;Centro
002;1;5.50;03/01/2025;V001;0007;Centro
```

Exemplo de cadastro:

```csv
ProCod;ProNom
001;Arroz
002;Feijão
```

## Definições dos indicadores

- `TotalVenda`: soma dos valores dos itens por DataVenda + Controle.
- `QuantidadeItens`: número de linhas de produtos por venda, mantido por
  compatibilidade. `QuantidadeUnidades`: soma da coluna Quantidade.
- Cliente retornou: tem mais de uma compra; retornos = compras menos um.
- Média por cliente: total vendido dividido pelo número de clientes distintos.
  Média por venda: total dividido pelo número de vendas. Denominador zero resulta
  em zero, sem NaN ou infinito na interface.
- O filtro de clientes identificados exclui `99999` e clientes vazios. Desmarcá-lo
  inclui essas vendas no total; clientes vazios não contam como cliente distinto.
- Semestres incluem o ano. Semanas começam na segunda-feira e terminam no domingo,
  inclusive quando cruzam anos. Dias da semana seguem a ordem de segunda a domingo.
- Valores usam a aritmética numérica do pandas, como no projeto original; o
  dashboard não substitui um livro contábil com aritmética decimal exata.

As tabelas de produtos, clientes e inspeção exibem 100 linhas por página, com
download completo. O gráfico de giro limita-se às 5.000 combinações com maior
quantidade e informa esse recorte; tabela/download preservam todos os registros.
Os caches de cálculos têm no máximo oito entradas e TTL de cinco minutos (quatro
entradas para exportação). A assinatura considera todas as linhas, esquema e índice.

Os downloads usam vírgula como separador e UTF-8 com BOM. Textos e cabeçalhos que
podem ser interpretados como fórmulas recebem apóstrofo protetor. Números negativos
continuam numéricos. A proteção destina-se à abertura inicial em planilhas; o
software de planilha pode alterar essa proteção ao salvar novamente o arquivo.
Os arquivos originais e os DataFrames da sessão não são alterados pela exportação.

## Arquitetura

```text
Home.py                 entrada e instruções
pages/                  navegação, filtros e apresentação
utils/dados.py          leitura, esquema e erros de entrada
utils/processamento.py  transformações e adaptadores públicos de carregamento
utils/analise.py        cálculos puros dos indicadores
utils/sessao.py         publicação dos dados e recuperação de falhas
utils/cache.py          cache limitado com assinatura integral
utils/visualizacao.py   paginação e download
utils/exportacao.py     geração de CSV seguro
utils/moeda.py          formatação monetária
tests/                  regressões unitárias e integração com Streamlit AppTest
```

Os cálculos podem ser chamados sem iniciar Streamlit. As funções públicas
`carregar_df_vendas`, `carregar_df_cadastro` e `processa_df_venda_agrupado`
continuam preenchendo as mesmas chaves de sessão e agora também retornam DataFrames.
`validar_df` continua entregando uma cópia para proteger a sessão de formatações.

## Desenvolvimento e validação

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt -c constraints-tested.txt
.\.venv\Scripts\python -m pip check
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m ruff format --check .
.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing
.\.venv\Scripts\python -m compileall -q Home.py pages utils tests
```

O CI está configurado para executar essas verificações em Python 3.11 e 3.13. O piso de cobertura de
linhas e ramificações dos utilitários é 85%; as páginas têm testes funcionais com
AppTest. Não há etapa de compilação de frontend ou empacotamento neste projeto.
Dados e `.streamlit/secrets.toml` estão ignorados pelo Git.

O [guia do material de apresentação](material_apresentacao/GUIA_DE_USO.md) descreve
as capturas, os gráficos e a demonstração com dados totalmente sintéticos. O pacote
público permite mostrar o projeto sem compartilhar o conjunto comercial.
