# Consultas da página

Cada pergunta da seção **Análises** (P1 a P6) tem de três a cinco *seguimentos*, e cada seguimento é **um arquivo `.sql`
desta pasta**: `pN_M.sql` é o seguimento `M` da pergunta `N` (`p1_0` é o mapa da P1; `p1_1` a 1ª pergunta seguinte).
A página mostra o SQL ao lado do gráfico e roda o mesmo arquivo no navegador, com DuckDB-WASM, sobre os marts em Parquet
que ela própria publica.

## Rodar no seu DuckDB, sem baixar nada

Os quatro marts que as consultas leem estão publicados em
`https://nandodsg.github.io/mercado-gestao-dados-br/dados/` (`mart_vaga_item.parquet`, `mart_vaga_ferramenta.parquet`,
`mart_vagas.parquet`, `mart_repost.parquet`). O arquivo [`_views.sql`](_views.sql) cria uma vista por tabela apontando pra
essas URLs; depois é só ler a consulta que quiser:

```bash
duckdb -c ".read consultas/_views.sql" -c ".read consultas/p1_2.sql"
```

Se já baixou os Parquet, troque as URLs de `_views.sql` pelo caminho local.

## Como cada consulta é conferida

- `pipeline/gerar_site.py` roda cada arquivo no DuckDB dos marts, monta o texto e os números da página a partir do resultado e
  grava tudo em `dados/pagina.json`: a página nunca traz um número que não saia de uma consulta daqui.
- `pipeline/check_consultas.py` (CI, nos workflows `pipeline` e `pages`) abre só os Parquet publicados, roda cada arquivo de
  novo e compara colunas e linhas com o `pagina.json`. Se uma consulta mudar sem a página refletir, ou o Parquet divergir do
  mart, a CI cai e a página não é trocada.
- Toda consulta termina em `order by`: a ordem das linhas faz parte do resultado.

## Convenções

- Uma consulta por arquivo, com um comentário de uma linha dizendo a pergunta (`-- P1·2 · …`).
- Só leem as quatro tabelas acima; nada de arquivo local nem de função de rede.
- A régua da diferença entre coordenação e gerência (teste exato de Fisher) é feita na página, não em SQL; as consultas
  trazem as contagens, e o intervalo de Wilson, quando aparece, é calculado em SQL.
