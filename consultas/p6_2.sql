-- P6·2 · vaga mais ampla tem referência salarial maior? mediana do ponto médio da faixa, vagas com as seis dimensões × as outras
with v as (
  select id_publico, nivel,
         count(distinct dimensao) filter (where dimensao not in ('Formação, idioma e experiência', 'Comportamental e condições')) as dimensoes,
         count(*) as itens
  from mart_vaga_item
  where item_chave <> 'outro' and nivel in ('coordenador', 'gerente')
  group by id_publico, nivel
)
select v.nivel,
       v.dimensoes = 6 as seis_dimensoes,
       count(*) as vagas,
       median((m.salario_min + m.salario_max) / 2) as mediana
from v
join mart_vagas m using (id_publico)
where m.salario_min is not null
group by all
order by v.nivel, seis_dimensoes desc;
