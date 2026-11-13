-- P4 · referência salarial pesquisada por nível: mediana do ponto médio da faixa (nunca "o que a vaga paga")
select nivel,
       count(*) as vagas,
       median((salario_min + salario_max) / 2) as mediana
from mart_vagas
where nivel in ('coordenador', 'gerente')
  and salario_min is not null
  and id_publico not in (select id_publico from mart_repost)
group by nivel
order by nivel;
