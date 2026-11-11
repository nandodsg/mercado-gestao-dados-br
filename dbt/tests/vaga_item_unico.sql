-- Vaga × item é a chave do mart: uma linha só.
select id_publico, item_chave, count(*) as n
from {{ ref('mart_vaga_item') }}
group by 1, 2
having count(*) > 1
