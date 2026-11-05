-- 1 linha por vaga publicada (contrato v1, data/vagas.csv). Tudo lido como texto e convertido aqui, pra uma coluna
-- fora do formato aparecer como erro de teste e não como erro de leitura.
select
    id_publico,
    empresa,
    cargo_oficial,
    nullif(modo, '')             as modo,
    nullif(geografia, '')        as geografia,
    nullif(regime, '')           as regime,
    nullif(cidade, '')           as cidade,
    nullif(uf, '')               as uf,
    nullif(contrato, '')         as contrato,
    nullif(fonte, '')            as fonte,
    nullif(candidatura_tipo, '') as candidatura_tipo,
    nullif(mes, '')              as mes,
    nullif(url, '')              as url,
    nullif(faixa_posting, '')    as faixa_posting,
    try_cast(nullif(salario_min, '') as double) as salario_min,
    try_cast(nullif(salario_max, '') as double) as salario_max,
    nullif(salario_moeda, '')    as salario_moeda,
    nullif(salario_tipo, '')     as salario_tipo
from read_csv('{{ var("data_dir") }}/vagas.csv', header = true, all_varchar = true)
