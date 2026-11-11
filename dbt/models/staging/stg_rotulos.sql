-- 1 linha por linha de anúncio rotulada (data/rotulos.csv). Sem texto da linha: só o hash dela, a posição, a seção,
-- a natureza, os itens (chaves da taxonomia separadas por `|`), as ferramentas citadas pelo nome (nomes canônicos do seed
-- `ferramentas`, separados por `|`) e o setor quando o item de setor aparece.
select
    id_publico,
    try_cast(ordem as integer) as ordem,
    hash_linha,
    secao,
    natureza,
    coalesce(itens, '')        as itens,
    coalesce(ferramentas, '')  as ferramentas,
    coalesce(setor, '')        as setor,
    versao_taxonomia,
    rotulador
from read_csv('{{ var("data_dir") }}/rotulos.csv', header = true, all_varchar = true)
