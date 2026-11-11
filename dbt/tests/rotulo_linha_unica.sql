-- Cada posição de cada anúncio é rotulada uma vez.
select id_publico, ordem, count(*) as n
from {{ ref('stg_rotulos') }}
group by 1, 2
having count(*) > 1
