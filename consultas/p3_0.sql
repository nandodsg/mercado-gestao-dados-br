-- P3 · o mapa: vagas com algum item de IA, e com IA aplicada ao negócio, por nível
with base as (
  select count(distinct id_publico) filter (where nivel = 'coordenador') as nc,
         count(distinct id_publico) filter (where nivel = 'gerente')     as ng
  from mart_vaga_item
)
select 'Algum item de IA' as item,
       count(distinct id_publico) filter (where nivel = 'coordenador') as coord,
       count(distinct id_publico) filter (where nivel = 'gerente')     as ger,
       round(100 * coord / any_value(nc)) as coord_pct,
       round(100 * ger / any_value(ng))   as ger_pct
from mart_vaga_item, base
where item_chave like 'ia.%'
union all
select item,
       count(distinct id_publico) filter (where nivel = 'coordenador'),
       count(distinct id_publico) filter (where nivel = 'gerente'),
       round(100 * count(distinct id_publico) filter (where nivel = 'coordenador') / any_value(nc)),
       round(100 * count(distinct id_publico) filter (where nivel = 'gerente') / any_value(ng))
from mart_vaga_item, base
where item_chave = 'ia.ia_aplicada'
group by item
order by coord_pct desc, item;
