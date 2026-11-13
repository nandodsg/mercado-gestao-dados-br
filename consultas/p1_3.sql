-- P1·3 · muda no que se faz ou no que se exige?
-- tarefa = a linha é responsabilidade; requisito = a linha é requisito
select item, nivel, count(*) as vagas,
       count(*) filter (where n_responsabilidade > 0 and n_requisito = 0) as so_tarefa,
       count(*) filter (where n_responsabilidade > 0 and n_requisito > 0) as tarefa_e_requisito,
       count(*) filter (where n_responsabilidade = 0 and n_requisito > 0) as so_requisito
from mart_vaga_item
where (item_chave = 'pessoas.operacao_time' and nivel = 'coordenador')
   or (item_chave = 'negocio.estrategia'    and nivel = 'gerente')
group by all
order by nivel;
