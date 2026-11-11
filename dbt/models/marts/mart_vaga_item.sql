-- Vaga × item da taxonomia: a unidade da análise ("quantas vagas pedem X"). Uma vaga conta uma vez por item, por mais
-- linhas que o citem; `n_linhas` e a divisão por natureza mostram quanto o anúncio insiste nele.
-- Anúncio repetido sai (`mart_repost`): conta uma vez.
select
    v.id_publico,
    v.nivel,
    t.chave   as item_chave,
    t.dimensao,
    t.item,
    count(*)                                          as n_linhas,
    count(*) filter (where i.natureza = 'responsabilidade') as n_responsabilidade,
    count(*) filter (where i.natureza = 'requisito')        as n_requisito
from {{ ref('stg_rotulo_itens') }} i
join {{ ref('mart_vagas') }} v on v.id_publico = i.id_publico
join {{ ref('taxonomia') }} t on t.chave = i.item
where i.id_publico not in (select id_publico from {{ ref('mart_repost') }})
group by all
