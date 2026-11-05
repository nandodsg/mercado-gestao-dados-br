-- Cobertura mínima de cidade: se menos que `cobertura_minima_cidade` das vagas têm cidade, a análise por cidade/UF
-- não se sustenta e o build falha (a linha devolvida traz a cobertura medida).
select
    count(*) filter (where cidade is not null) * 1.0 / nullif(count(*), 0) as cobertura,
    {{ var('cobertura_minima_cidade') }} as minimo
from {{ ref('mart_vagas') }}
having count(*) filter (where cidade is not null) * 1.0 / nullif(count(*), 0) < {{ var('cobertura_minima_cidade') }}
