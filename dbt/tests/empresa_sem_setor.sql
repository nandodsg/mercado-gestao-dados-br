{{ config(severity='warn') }}
-- Aviso (não trava a CI nem a publicação da página): empresa que aparece em vagas.csv sem linha em empresas.csv. O setor da
-- empresa só alimenta a junção de grafias do `mart_repost`; sem a linha, a empresa entra com o próprio nome (coalesce) e
-- segue sem setor. A CI lista os nomes. As empresas fictícias de tests/fixtures ("Empresa Exemplo …") ficam de fora: a
-- fixture existe pra testar o pipeline, não o dicionário de setores.
select distinct v.empresa
from {{ ref('stg_vagas') }} v
left join {{ ref('stg_empresas') }} s on s.empresa = v.empresa
where s.empresa is null
  and v.empresa not like 'Empresa Exemplo %'
