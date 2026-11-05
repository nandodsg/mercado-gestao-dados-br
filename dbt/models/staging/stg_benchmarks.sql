-- 1 linha por fonte de benchmark salarial pesquisada por vaga (data/benchmarks.csv). Referência de mercado, nunca o
-- que a vaga paga (camada 2 da transparência salarial; a camada 1 é salario_* em stg_vagas).
select
    id_publico,
    try_cast(ordem as integer) as ordem,
    fonte_url,
    nullif(fonte_nota, '') as fonte_nota
from read_csv('{{ var("data_dir") }}/benchmarks.csv', header = true, all_varchar = true)
