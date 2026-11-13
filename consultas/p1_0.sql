-- P1 · o mapa: % das vagas que pedem cada item, por nível
with base as (
  select count(distinct id_publico) filter (where nivel = 'coordenador') as nc,
         count(distinct id_publico) filter (where nivel = 'gerente')     as ng
  from mart_vaga_item
), k as (
  select item,
         count(distinct id_publico) filter (where nivel = 'coordenador') as coord,
         count(distinct id_publico) filter (where nivel = 'gerente')     as ger
  from mart_vaga_item
  where item_chave in ('pessoas.liderar_time', 'negocio.stakeholders', 'pessoas.desenvolver_pessoas',
                       'negocio.visao_negocio', 'analytics.analise_insights',
                       'negocio.estrategia', 'pessoas.operacao_time', 'pessoas.contratar_estruturar',
                       'experiencia.anos', 'ia.ia_aplicada')
  group by item
)
select item, coord, ger,
       round(100 * coord / nc) as coord_pct,
       round(100 * ger / ng)   as ger_pct
from k, base
order by abs(ger_pct - coord_pct), item;
