-- Vaga × ferramenta é a chave do mart: uma linha só.
select id_publico, ferramenta, count(*) as n
from {{ ref('mart_vaga_ferramenta') }}
group by 1, 2
having count(*) > 1
