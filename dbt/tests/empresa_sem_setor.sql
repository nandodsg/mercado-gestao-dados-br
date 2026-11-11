-- Toda empresa que aparece em vagas.csv precisa ter linha em setores.csv. Vaga nova de empresa nova falha aqui, em vez
-- de cair sem setor na análise. As empresas fictícias de tests/fixtures ("Empresa Exemplo …") ficam de fora: a fixture
-- existe pra testar o pipeline, não o dicionário de setores.
select distinct v.empresa
from {{ ref('stg_vagas') }} v
left join {{ ref('setores') }} s on s.empresa = v.empresa
where s.empresa is null
  and v.empresa not like 'Empresa Exemplo %'
