-- P4·3 · quem não diz o salário diz o quê? o dado publicado diz se o anúncio tem seção de benefícios, não o que ela contém
select nivel,
       count(*) as vagas,
       count(*) filter (where tem_beneficios) as com_secao_beneficios
from mart_vagas
where nivel in ('coordenador', 'gerente')
group by nivel
order by nivel;
