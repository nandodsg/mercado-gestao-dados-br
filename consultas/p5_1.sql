-- P5·1 · qual setor pede qual tipo? vagas por setor da empresa e tipo da cadeira
with dims as (
  select id_publico, nivel, dimensao, sum(n_linhas) as linhas
  from mart_vaga_item
  where nivel in ('coordenador', 'gerente')
    and dimensao not in ('Formação, idioma e experiência', 'Comportamental e condições')
  group by all
), dom as (
  select *, row_number() over (partition by id_publico order by linhas desc, dimensao) as rn
  from dims
)
select coalesce(v.setor, 'não informado') as setor,
       d.dimensao as tipo,
       count(*) as vagas
from dom d
join mart_vagas v using (id_publico)
where d.rn = 1
group by all
order by setor, vagas desc, tipo;
