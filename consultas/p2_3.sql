-- P2·3 · o técnico é obrigatório ou diferencial? das 6 ferramentas mais citadas, em quantas vagas ela só aparece em "diferenciais"
select ferramenta,
       count(*) as vagas,
       count(*) filter (where n_diferencial = n_linhas) as so_diferencial
from mart_vaga_ferramenta
where nivel in ('coordenador', 'gerente')
group by ferramenta
order by vagas desc, ferramenta
limit 6;
