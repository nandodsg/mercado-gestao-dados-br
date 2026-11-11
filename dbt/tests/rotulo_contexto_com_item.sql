-- Linha de contexto (descreve a empresa ou a vaga, não pede nada) não carrega item.
select id_publico, ordem, itens
from {{ ref('stg_rotulos') }}
where natureza = 'contexto' and itens <> ''
