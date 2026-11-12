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

-- ATS lido do host da URL (que já é pública), pelo seed ats_hosts.csv: o host do anúncio termina no padrão. Vale o padrão mais
-- longo. URL sem padrão conhecido = página de carreiras da própria empresa; sem URL = sem ATS.
ats_casado as (
    select
        b.id_publico,
        h.ats,
        row_number() over (partition by b.id_publico order by length(h.host) desc) as rn
    from base b
    join {{ ref('ats_hosts') }} h
      on lower(regexp_extract(b.url, 'https?://([^/:]+)', 1)) = h.host
      or lower(regexp_extract(b.url, 'https?://([^/:]+)', 1)) like '%.' || h.host
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
    b.mes,
    b.data_publicacao,
    b.data_captura,
    b.data_analise,
    b.idioma,
    b.tem_sobre_empresa,
    b.tem_beneficios,
    b.url,
    b.faixa_posting,
    b.salario_min,
    b.salario_max,
    b.salario_moeda,
    b.salario_tipo,
    coalesce(a.ats, case when b.url is not null then 'Site de carreiras da empresa' end) as ats,
    e.setor,
    (select count(*) from {{ ref('stg_requisitos') }} r where r.id_publico = b.id_publico) as n_requisitos,
    (select count(*) from {{ ref('stg_benchmarks') }} k where k.id_publico = b.id_publico) as n_benchmarks
from base b
left join casadas c on c.id_publico = b.id_publico and c.rn = 1
left join ats_casado a on a.id_publico = b.id_publico and a.rn = 1
left join {{ ref('stg_empresas') }} e on e.empresa = b.empresa
