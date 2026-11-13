-- P4·2 · CLT × PJ: vagas por tipo de contrato declarado, e quantas têm referência salarial
select nivel,
       coalesce(contrato, 'não informado') as contrato,
       count(*) as vagas,
       count(salario_min) as com_referencia
from mart_vagas
where nivel in ('coordenador', 'gerente')
group by all
order by nivel, vagas desc, contrato;
