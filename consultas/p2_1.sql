-- P2·1 · quais ferramentas, por nível? as 10 citadas pelo nome em mais vagas (regra fixa, sem modelo)
with base as (
  select count(distinct id_publico) filter (where nivel = 'coordenador') as nc,
         count(distinct id_publico) filter (where nivel = 'gerente')     as ng
  from mart_vaga_item
), f as (
  select ferramenta as item,
         count(distinct id_publico) filter (where nivel = 'coordenador') as coord,
         count(distinct id_publico) filter (where nivel = 'gerente')     as ger
  from mart_vaga_ferramenta
  group by ferramenta
)
select item, coord, ger,
       round(100 * coord / nc) as coord_pct,
       round(100 * ger / ng)   as ger_pct
from f, base
order by coord + ger desc, item
limit 10;
