-- O arquivo publicado carrega uma só versão da taxonomia (rodada com taxonomia nova substitui a anterior).
select count(distinct versao_taxonomia) as versoes
from {{ ref('stg_rotulos') }}
having count(distinct versao_taxonomia) > 1
