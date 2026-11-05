-- Vagas com o bucket de nível. Regra = seed niveis.csv: a primeira linha por `ordem` cujo padrão (regex) bate no cargo
-- vence; `empresa`, quando preenchida, restringe a linha àquela empresa. Cargo e empresa sem acento e em minúsculas.
-- Nada casou → 'outros'. Determinística e sem LLM de propósito: nível é a chave da análise.
with base as (
    select
        *,
        strip_accents(lower(cargo_oficial)) as cargo_norm,
        strip_accents(lower(empresa))       as empresa_norm
    from {{ ref('stg_vagas') }}
),

casadas as (
    select
        b.id_publico,
        n.bucket,
        n.ordem,
        row_number() over (partition by b.id_publico order by n.ordem) as rn
    from base b
    join {{ ref('niveis') }} n
      on regexp_matches(b.cargo_norm, n.padrao)
     and (n.empresa is null or n.empresa = '' or n.empresa = b.empresa_norm)
)

select
    b.id_publico,
    b.empresa,
    b.cargo_oficial,
    coalesce(c.bucket, 'outros') as nivel,
    c.ordem                      as nivel_regra,
    b.modo,
    b.geografia,
    b.regime,
    b.cidade,
    b.uf,
    b.contrato,
    b.fonte,
    b.candidatura_tipo,
    b.mes,
    b.url,
    b.faixa_posting,
    b.salario_min,
    b.salario_max,
    b.salario_moeda,
    b.salario_tipo,
    (select count(*) from {{ ref('stg_requisitos') }} r where r.id_publico = b.id_publico) as n_requisitos,
    (select count(*) from {{ ref('stg_benchmarks') }} k where k.id_publico = b.id_publico) as n_benchmarks
from base b
left join casadas c on c.id_publico = b.id_publico and c.rn = 1
