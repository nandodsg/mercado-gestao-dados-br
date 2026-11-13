-- P5 · o mapa: o tipo da cadeira é a dimensão com mais linhas no anúncio, entre as seis de conteúdo (empate: ordem alfabética)
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
select dimensao as tipo,
       count(*) filter (where nivel = 'coordenador') as coord,
       count(*) filter (where nivel = 'gerente')     as ger
from dom
where rn = 1
group by dimensao
order by coord + ger desc, tipo;
