-- 1 linha por linha rotulada × item: o campo `itens` aberto pelo separador `|`. Linha de contexto (sem item) não aparece.
select
    id_publico,
    ordem,
    hash_linha,
    secao,
    natureza,
    unnest(string_split(itens, '|')) as item
from {{ ref('stg_rotulos') }}
where itens <> ''
