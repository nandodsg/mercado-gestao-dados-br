-- P2 · o mapa: quantas vagas pedem mão na massa (referência técnica / hands-on), por nível
select nivel,
       count(distinct id_publico) as vagas_pedem,
       (select count(distinct id_publico) from mart_vaga_item t where t.nivel = i.nivel) as vagas
from mart_vaga_item i
where item_chave = 'pessoas.hands_on' and nivel in ('coordenador', 'gerente')
group by nivel
order by nivel;
