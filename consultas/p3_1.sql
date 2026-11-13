-- P3·1 · tarefa, requisito ou diferencial? vagas com IA em cada papel (uma vaga pode ter mais de um)
-- tarefa = linha de responsabilidade · diferencial = linha da seção de diferenciais · requisito = o resto das linhas de requisito
with base as (
  select count(distinct id_publico) filter (where nivel = 'coordenador') as nc,
         count(distinct id_publico) filter (where nivel = 'gerente')     as ng
  from mart_vaga_item
)
select papel as item,
       count(distinct id_publico) filter (where nivel = 'coordenador') as coord,
       count(distinct id_publico) filter (where nivel = 'gerente')     as ger,
       round(100 * coord / any_value(nc)) as coord_pct,
       round(100 * ger / any_value(ng))   as ger_pct
from (
  select id_publico, nivel, 'Como tarefa' as papel from mart_vaga_item where item_chave like 'ia.%' and n_responsabilidade > 0
  union all
  select id_publico, nivel, 'Como requisito' from mart_vaga_item where item_chave like 'ia.%' and n_requisito - least(n_requisito, n_diferencial) > 0
  union all
  select id_publico, nivel, 'Como diferencial' from mart_vaga_item where item_chave like 'ia.%' and n_diferencial > 0
), base
where nivel in ('coordenador', 'gerente')
group by papel
order by papel;
