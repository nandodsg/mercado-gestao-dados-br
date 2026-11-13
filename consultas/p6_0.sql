-- P6 · o mapa: quantas vagas pedem as seis dimensões de conteúdo (pessoas, estratégia, engenharia, analytics, IA, governança)
with v as (
  select id_publico, nivel,
         count(distinct dimensao) filter (where dimensao not in ('Formação, idioma e experiência', 'Comportamental e condições')) as dimensoes,
         count(*) as itens
  from mart_vaga_item
  where item_chave <> 'outro' and nivel in ('coordenador', 'gerente')
  group by id_publico, nivel
)
select nivel,
       count(*) as vagas,
       count(*) filter (where dimensoes = 6) as seis_dimensoes,
       median(itens) as itens_mediana,
       min(itens) as itens_min,
       max(itens) as itens_max
from v
group by nivel
order by nivel;
