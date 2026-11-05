-- Contagem por nível: a conferência mais simples do universo (o Item 8 parte daqui). n = vagas, nunca percentual sozinho.
select
    nivel,
    count(*)                                          as n_vagas,
    count(*) filter (where cidade is not null)        as n_com_cidade,
    count(*) filter (where faixa_posting is not null) as n_com_faixa_no_posting,
    sum(n_requisitos)                                 as n_requisitos
from {{ ref('mart_vagas') }}
group by nivel
order by n_vagas desc
