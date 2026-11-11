-- Quanto do universo de anúncios já foi classificado. Resultado parcial é estado normal enquanto uma rodada está em curso.
select
    c.linhas,
    c.rotuladas,
    (select count(*) from {{ ref('stg_rotulos') }}) as linhas_no_csv,
    (select count(distinct id_publico) from {{ ref('stg_rotulos') }}) as vagas_com_rotulo,
    case when c.linhas = 0 then 0 else c.rotuladas * 1.0 / c.linhas end as fracao
from {{ ref('stg_cobertura') }} c
