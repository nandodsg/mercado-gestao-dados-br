# Plano

Registro de decisões do pipeline do repo público: o que mudou o desenho e por quê. Sem números do dataset (eles vêm do
`manifest.json` a cada publicação).

## Estado

| peça | estado |
|---|---|
| Esqueleto (README, licenças, `.gitignore`) | pronto |
| `pipeline/check_data.py` (contrato, manifest, sigilo) | pronto, testado sobre `tests/fixtures` |
| `dbt/` (staging, marts por nível, testes) | `dbt build` verde **sobre os dados fictícios**; **não rodado sobre dado real** |
| CI `pipeline.yml` | pronta; roda sobre `data/` quando existir e sobre `tests/fixtures` antes disso |
| Pages `pages.yml` + `site/` | pronto; `site/` é um marcador até a página de verdade |
| Seeds `setores.csv`, `taxonomia.csv`, `overrides.csv` | ainda não existem: nascem junto com o conjunto de referência e a classificação |
| Pasta `data/` | não existe: só a publicação automática escreve, na 1ª vez |

Pendência: o 1º `dbt build` com dado real depende da 1ª publicação. Na 1ª rodada, conferir (a) os valores de `regime`
contra `presencial | hibrido | remoto` (o teste só avisa) e (b) se as regras de `niveis.csv` que citam `empresa` casam: elas
comparam o nome da empresa sem acento e em minúsculas, então um nome escrito diferente cairia em `outros` sem erro.

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

## Próximos passos (gatilhos)

- **Taxonomia, setores e conjunto de referência** → seeds `taxonomia.csv`, `setores.csv`, `overrides.csv` e o teste "100% dos
  requisitos classificados". Gatilho: método do conjunto de referência decidido.
- **Classificação em produção** (`pipeline/`, cache por sha256 do texto, `overrides.csv` vence o modelo). Gatilho: modelo
  escolhido por comparação num conjunto rotulado. **Aqui reavaliar Dagster** (ativos com cache e reprocesso).
- **Página com números e consultas** (`site/`, DuckDB-WASM sobre os marts). Gatilho: achados revisados.
