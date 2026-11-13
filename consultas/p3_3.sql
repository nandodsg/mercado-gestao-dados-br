-- P3·3 · a IA aparece junto de quê? % das vagas que pedem cada item, entre as que têm IA e as que não têm (os dois níveis juntos)
with vagas as (
  select id_publico, bool_or(item_chave like 'ia.%') as tem_ia
  from mart_vaga_item where nivel in ('coordenador', 'gerente')
  group by id_publico
), n as (
  select count(*) filter (where tem_ia) as n_com, count(*) filter (where not tem_ia) as n_sem from vagas
), k as (
  select i.item,
         count(distinct i.id_publico) filter (where v.tem_ia)     as com_ia,
         count(distinct i.id_publico) filter (where not v.tem_ia) as sem_ia
  from mart_vaga_item i
  join vagas v using (id_publico)
  where i.item_chave in ('negocio.produto_dados', 'gov.governanca', 'eng.plataforma_cloud', 'analytics.kpis_metricas',
                         'negocio.estrategia', 'eng.pipelines')
  group by i.item
)
select item, com_ia, n_com as base_com_ia, sem_ia, n_sem as base_sem_ia,
       round(100 * com_ia / n_com) as pct_com_ia,
       round(100 * sem_ia / n_sem) as pct_sem_ia
from k, n
order by abs(100 * com_ia / n_com - 100 * sem_ia / n_sem) desc, item;
