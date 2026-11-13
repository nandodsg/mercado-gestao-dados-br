-- As quatro tabelas da página, lidas dos Parquet que ela publica (sem baixar nada). Rode antes de qualquer consulta desta pasta:
--   duckdb -c ".read consultas/_views.sql" -c ".read consultas/p1_2.sql"
-- Troque a URL pelo caminho local (dados/*.parquet) se já tiver baixado os arquivos.
create or replace view mart_vaga_item      as select * from 'https://nandodsg.github.io/mercado-gestao-dados-br/dados/mart_vaga_item.parquet';
create or replace view mart_vaga_ferramenta as select * from 'https://nandodsg.github.io/mercado-gestao-dados-br/dados/mart_vaga_ferramenta.parquet';
create or replace view mart_vagas          as select * from 'https://nandodsg.github.io/mercado-gestao-dados-br/dados/mart_vagas.parquet';
create or replace view mart_repost         as select * from 'https://nandodsg.github.io/mercado-gestao-dados-br/dados/mart_repost.parquet';
