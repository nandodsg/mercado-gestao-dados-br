-- 1 linha por linha rotulada × ferramenta citada pelo nome: o campo `ferramentas` aberto pelo separador `|`.
-- A regra é determinística (seed `ferramentas`, aplicada às linhas do anúncio antes da publicação), não do modelo.
select
    id_publico,
    ordem,
    hash_linha,
    secao,
    natureza,
    unnest(string_split(ferramentas, '|')) as ferramenta
from {{ ref('stg_rotulos') }}
where ferramentas <> ''
