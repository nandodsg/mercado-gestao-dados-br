-- P1·4 · vale dentro da mesma empresa? empresas com vaga nos dois níveis
select v.empresa,
       count(distinct i.id_publico) filter (where i.nivel = 'coordenador') as coord,
       count(distinct i.id_publico) filter (where i.nivel = 'gerente')     as ger
from mart_vaga_item i
join mart_vagas v using (id_publico)
group by v.empresa
having coord > 0 and ger > 0
order by v.empresa;
