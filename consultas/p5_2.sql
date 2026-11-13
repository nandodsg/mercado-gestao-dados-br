-- P5·2 · o tipo muda a referência salarial? mediana do ponto médio da faixa, por tipo da cadeira
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
select d.dimensao as tipo,
       count(*) as vagas,
       median((v.salario_min + v.salario_max) / 2) as mediana
from dom d
join mart_vagas v using (id_publico)
where d.rn = 1
  and v.salario_min is not null
group by d.dimensao
order by vagas desc, tipo;
