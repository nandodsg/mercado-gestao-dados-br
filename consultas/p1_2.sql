-- P1·2 · o que mais muda? itens com 15 pontos ou mais de diferença (gerência − coordenação)
-- o selo (Fisher, régua do p) a página calcula sobre as mesmas contagens
with base as (
  select count(distinct id_publico) filter (where nivel = 'coordenador') as nc,
         count(distinct id_publico) filter (where nivel = 'gerente')     as ng
  from mart_vaga_item
), k as (
  select item,
         count(distinct id_publico) filter (where nivel = 'coordenador') as coord,
         count(distinct id_publico) filter (where nivel = 'gerente')     as ger
  from mart_vaga_item
  where item_chave <> 'outro'
  group by item
)
select item, coord, ger,
       round(100 * ger / ng) - round(100 * coord / nc) as diferenca_pontos
from k, base
where abs(round(100 * ger / ng) - round(100 * coord / nc)) >= 15
order by diferenca_pontos desc, item;
