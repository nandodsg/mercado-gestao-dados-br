-- P6·1 · quantas dimensões de conteúdo uma vaga pede, por nível
with v as (
  select id_publico, nivel,
         count(distinct dimensao) filter (where dimensao not in ('Formação, idioma e experiência', 'Comportamental e condições')) as dimensoes,
         count(*) as itens
  from mart_vaga_item
  where item_chave <> 'outro' and nivel in ('coordenador', 'gerente')
  group by id_publico, nivel
)
select dimensoes,
       count(*) filter (where nivel = 'coordenador') as coord,
       count(*) filter (where nivel = 'gerente')     as ger
from v
group by dimensoes
order by dimensoes;
