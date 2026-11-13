-- P2·2 · quem pede mão na massa pede mais ferramenta? ferramentas citadas pelo nome por vaga, média
with vagas as (
  select distinct id_publico, nivel from mart_vaga_item where nivel in ('coordenador', 'gerente')
), mm as (
  select distinct id_publico from mart_vaga_item where item_chave = 'pessoas.hands_on'
), nf as (
  select id_publico, count(*) as n from mart_vaga_ferramenta group by id_publico
)
select v.nivel,
       v.id_publico in (select id_publico from mm) as mao_na_massa,
       count(*) as vagas,
       round(avg(coalesce(nf.n, 0)), 1) as ferramentas_por_vaga
from vagas v
left join nf using (id_publico)
group by all
order by v.nivel, mao_na_massa desc;
