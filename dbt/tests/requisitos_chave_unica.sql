-- (id_publico, ordem) é a chave de requisitos.csv e de benchmarks.csv.
select 'requisitos' as arquivo, id_publico, ordem, count(*) as n
from {{ ref('stg_requisitos') }} group by all having count(*) > 1
union all
select 'benchmarks', id_publico, ordem, count(*)
from {{ ref('stg_benchmarks') }} group by all having count(*) > 1
