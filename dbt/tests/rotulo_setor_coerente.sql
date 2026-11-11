-- O setor só existe junto do item de setor, e vem da lista fechada de setores (seed `lista_setores`).
with s as (select setor from {{ ref('lista_setores') }})
select r.id_publico, r.ordem, r.setor, r.itens
from {{ ref('stg_rotulos') }} r
where (r.setor <> '' and r.setor <> 'nenhum' and r.setor not in (select setor from s))
   or ((r.setor not in ('', 'nenhum')) <> list_contains(string_split(r.itens, '|'), 'experiencia.setor'))
