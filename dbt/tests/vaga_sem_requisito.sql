-- Toda vaga publicada tem pelo menos uma linha de requisito.
select id_publico, empresa, cargo_oficial
from {{ ref('mart_vagas') }}
where n_requisitos = 0
