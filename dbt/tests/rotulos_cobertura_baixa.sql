-- Aviso (não derruba o build): nem toda linha de anúncio foi rotulada, ou o CSV não bate com a cobertura do manifest.
-- Rodada parcial é o estado normal durante uma classificação e não pode deixar a CI vermelha.
{{ config(severity='warn') }}
select linhas, rotuladas, linhas_no_csv, fracao
from {{ ref('mart_cobertura_rotulos') }}
where fracao < 1 or linhas_no_csv <> rotuladas
