-- Aviso (não derruba o build): mais de 15% das vagas em 'outros' costuma ser regra faltando em niveis.csv ou empresa
-- escrita diferente da normalizada (as regras com `empresa` comparam empresa sem acento e em minúsculas).
{{ config(severity='warn') }}
select count(*) filter (where nivel = 'outros') * 1.0 / count(*) as fracao_outros
from {{ ref('mart_vagas') }}
having count(*) filter (where nivel = 'outros') * 1.0 / count(*) > 0.15
