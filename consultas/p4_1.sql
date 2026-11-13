-- P4·1 · as fontes concordam entre si? o dado publicado diz quantas fontes cada vaga tem, não o valor de cada uma
select nivel,
       count(*) as vagas,
       count(*) filter (where n_benchmarks > 0) as vagas_com_referencia,
       sum(n_benchmarks) as fontes_citadas
from mart_vagas
where nivel in ('coordenador', 'gerente')
group by nivel
order by nivel;
