-- Vaga × ferramenta citada pelo nome no anúncio: a unidade da análise ("quantas vagas citam Python"), com a mesma base de
-- `mart_vaga_item` (vagas com o anúncio classificado, anúncio repetido fora). Uma vaga conta uma vez por ferramenta, por
-- mais linhas que a citem; `n_linhas` e a divisão por natureza mostram quanto o anúncio insiste nela.
select
    v.id_publico,
    v.nivel,
    f.ferramenta,
    count(*)                                                as n_linhas,
    count(*) filter (where f.natureza = 'responsabilidade') as n_responsabilidade,
    count(*) filter (where f.natureza = 'requisito')        as n_requisito,
    count(*) filter (where f.secao = 'diferenciais')       as n_diferencial
from {{ ref('stg_rotulo_ferramentas') }} f
join {{ ref('mart_vagas') }} v on v.id_publico = f.id_publico
where f.id_publico in (select id_publico from {{ ref('mart_vaga_item') }})
group by all
