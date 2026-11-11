-- Cobertura declarada no manifest: linhas de anúncio no universo × linhas já rotuladas.
select
    cobertura.linhas    as linhas,
    cobertura.rotuladas as rotuladas
from read_json('{{ var("data_dir") }}/manifest.json')
