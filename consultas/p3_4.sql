-- P3·4 · a IA muda por setor? vagas com algum item de IA, por setor da empresa
select coalesce(v.setor, 'não informado') as setor,
       count(distinct i.id_publico) as vagas,
       count(distinct i.id_publico) filter (where i.id_publico in (select id_publico from mart_vaga_item where item_chave like 'ia.%')) as com_ia
from mart_vaga_item i
join mart_vagas v using (id_publico)
where i.nivel in ('coordenador', 'gerente')
group by all
order by vagas desc, setor;
