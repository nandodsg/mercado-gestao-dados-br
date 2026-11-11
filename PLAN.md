# Plano

Registro de decisões do pipeline do repo público: o que mudou o desenho e por quê. Sem números do dataset (eles vêm do
`manifest.json` a cada publicação).

## Estado

| peça | estado |
|---|---|
| Esqueleto (README, licenças, `.gitignore`) | pronto |
| `pipeline/check_data.py` (contrato, manifest, sigilo) | pronto, testado sobre `tests/fixtures` |
| `dbt/` (staging, marts por nível, testes) | `dbt build` verde sobre os dados fictícios e **sobre o dado real da 1ª publicação** |
| CI `pipeline.yml` | verde sobre `data/` (1ª publicação, 2026-11-05); sem `data/`, roda sobre `tests/fixtures` |
| Pages `pages.yml` + `site/` | pronto; `site/` é um marcador até a página de verdade |
| Seeds `setores.csv`, `taxonomia.csv`, `overrides.csv` | ainda não existem: nascem junto com o conjunto de referência e a classificação |
| Pasta `data/` | publicada pela automação (1 commit por publicação) |

Conferido na 1ª publicação com dado real: os valores de `regime` batem com `presencial | hibrido | remoto` (sem avisos) e
as regras de `niveis.csv` que citam `empresa` casam (as contagens por nível bateram com as da origem). Observação: `regime`
vem vazio em parte das vagas (o teste de valores aceitos ignora vazio); análises por regime devem informar o `n` com regime.

## Decisões

| data | decisão | por quê |
|---|---|---|
| 2026-11-04 | Nome do repo `mercado-gestao-dados-br` | escolhido na abertura do projeto |
| 2026-11-04 | Repo público, criado já com um commit inicial | a API do GitHub recusa o 1º commit de automação num repo vazio |
| 2026-11-04 | `data/` é escrito só pela publicação automática (1 commit por publicação) | o dado nasce num banco privado; edição manual de CSV quebra a rastreabilidade pelo `manifest.json` |
| 2026-11-04 | dbt sobre **DuckDB**, sem warehouse | CI sem credencial de banco e sem custo; o mesmo DuckDB roda na página (DuckDB-WASM) mais tarde |
| 2026-11-04 | Staging lê tudo como texto e converte no SQL | coluna fora do formato vira falha de teste legível, não erro de leitura de CSV |
| 2026-11-04 | Nível = regra determinística em seed (`niveis.csv`), sem modelo de linguagem | nível é a chave da análise e precisa ser reproduzível; regex só no subconjunto que o DuckDB entende |
| 2026-11-04 | `check_data.py` repete a checagem de sigilo da publicação | defesa em profundidade: este repo é público e não confia em quem escreve em `data/` |
| 2026-11-04 | CI antes da 1ª publicação roda sobre `tests/fixtures` (dados fictícios, domínio `.invalid`) | o esqueleto fica testado desde o 1º dia |
| 2026-11-04 | Licenças: CC BY 4.0 pro dado, MIT pro código | CC BY pede só crédito, o que serve a quem quer citar |
| 2026-11-04 | Único secret futuro: chave do gateway de LLM (classificação), com teto de gasto | tudo o mais dispensa credencial |
| 2026-11-05 | README sem vocabulário interno do app de origem e sem retrato de data (contagens, concentrações) | o leitor externo não conhece o app; o dado se atualiza toda semana, então número só vem do `manifest.json`, do mart ou da página |
| 2026-11-05 | Arquitetura: **armazenamento = CSVs no git; DuckDB só como motor de consulta, reconstruído a cada execução; dbt = transformação**; sem catálogo nem formato de lakehouse | um escritor, rodada semanal, git já guarda os snapshots; "data lake" seria nome grande demais pra poucos CSVs pequenos |
| 2026-11-05 | Análise geográfica fora do foco: o README diz que a distribuição por local não é representativa (reflete a preferência de busca do autor) e recomenda a composição dos requisitos como fato principal | a amostra não pretende refletir a distribuição nacional; qualquer estudo de mercado mostraria concentração em São Paulo de qualquer forma |
| 2026-11-05 | Orquestração = GitHub Actions encadeadas por commit em `data/`; **sem Dagster por enquanto** | uma transformação (o DAG é o do dbt) e um encadeamento simples; reavaliar quando entrar a classificação por modelo de linguagem (custo, cache, reprocesso parcial) |
| 2026-11-11 | Modelo de classificação: **Claude Haiku 5.5**, consumido pela **assinatura do autor** (cota semanal), não por API paga. Rota por gateway documentada e com exemplo (`pipeline/exemplo_gateway.py`); a decisão de como a rota por assinatura é disparada fica em aberto (próximo passo abaixo). Substitui, para a classificação, a linha "único secret futuro: chave do gateway" | o volume é pequeno (cache por texto: só linha nova gasta), o modelo é barato e a cota da assinatura já está paga; o gateway segue viável se a rota mudar |

## Próximos passos (gatilhos)

- **Taxonomia, setores e conjunto de referência** → seeds `taxonomia.csv`, `setores.csv`, `overrides.csv` e o teste "100% dos
  requisitos classificados". Gatilho: método do conjunto de referência decidido.
- **Rota de consumo por assinatura** (antes da classificação em produção). Planejar como a classificação é disparada e como o
  resultado volta ao repositório sem chave de API e sem publicar o anúncio inteiro; medir o Haiku 5.5 **por essa rota** contra a
  referência (a medição atual foi por API com esquema estrito; a rota por assinatura tem outro envelope e pode render diferente).
  Gatilho: modelo escolhido (feito, 2026-11-11).
- **Classificação em produção** (`pipeline/`, cache por sha256 do texto, `overrides.csv` vence o modelo). Gatilho: modelo
  escolhido por comparação num conjunto rotulado. **Aqui reavaliar Dagster** (ativos com cache e reprocesso).
- **Página com números e consultas** (`site/`, DuckDB-WASM sobre os marts). Gatilho: achados revisados.
