-- Anúncio repetido: a mesma empresa publica o mesmo texto mais de uma vez (às vezes com outro título). Conta uma vez só
-- na análise vaga × item. Critério: mesma empresa normalizada (`stg_empresas`), mesmo nível e o MESMO conjunto de linhas
-- rotuladas (hash de cada linha do anúncio). Igualdade exata de propósito: anúncios da mesma empresa que só dividem o
-- texto institucional não são repetição. A vaga mais antiga (mês, depois id) fica; as outras apontam pra ela.
-- O mesmo texto publicado em níveis diferentes conta uma vez em cada nível: é a comparação entre níveis que a análise faz.
with assinatura as (
    select id_publico, string_agg(distinct hash_linha, ',' order by hash_linha) as linhas
    from {{ ref('stg_rotulos') }}
    group by id_publico
),

grupos as (
    select
        v.id_publico,
        v.mes,
        coalesce(s.empresa_normalizada, v.empresa) as empresa,
        v.nivel,
        a.linhas
    from {{ ref('mart_vagas') }} v
    join assinatura a using (id_publico)
    left join {{ ref('stg_empresas') }} s on s.empresa = v.empresa
),

ordenados as (
    select
        *,
        first_value(id_publico) over (partition by empresa, nivel, linhas order by mes, id_publico) as original
    from grupos
)

select id_publico, original as repost_de, empresa, nivel
from ordenados
where id_publico <> original
