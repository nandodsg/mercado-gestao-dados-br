-- P2·4 · que stack aparece junta? pares de ferramentas citadas na mesma vaga
select a.ferramenta as ferramenta_a,
       b.ferramenta as ferramenta_b,
       count(*) as vagas,
       (select count(distinct id_publico) from mart_vaga_item where nivel in ('coordenador', 'gerente')) as base
from mart_vaga_ferramenta a
join mart_vaga_ferramenta b
  on a.id_publico = b.id_publico and a.ferramenta < b.ferramenta
where a.nivel in ('coordenador', 'gerente')
group by a.ferramenta, b.ferramenta
order by vagas desc, ferramenta_a, ferramenta_b
limit 10;
