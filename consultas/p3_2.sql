-- P3·2 · que IA? os seis itens de IA da lista, % das vagas por nível
with base as (
  select count(distinct id_publico) filter (where nivel = 'coordenador') as nc,
         count(distinct id_publico) filter (where nivel = 'gerente')     as ng
  from mart_vaga_item
)
select item,
       count(distinct id_publico) filter (where nivel = 'coordenador') as coord,
       count(distinct id_publico) filter (where nivel = 'gerente')     as ger,
       round(100 * coord / any_value(nc)) as coord_pct,
       round(100 * ger / any_value(ng))   as ger_pct
from mart_vaga_item, base
where item_chave like 'ia.%'
group by item
order by coord + ger desc, item;
