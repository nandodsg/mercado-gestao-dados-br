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
    nullif(mes, '')              as mes,
    try_cast(nullif(data_publicacao, '') as date) as data_publicacao,
    try_cast(nullif(data_captura, '') as date)    as data_captura,
    try_cast(nullif(data_analise, '') as date)    as data_analise,
    nullif(idioma, '')           as idioma,
    case lower(tem_sobre_empresa) when 'true' then true when 'false' then false end as tem_sobre_empresa,
    case lower(tem_beneficios)    when 'true' then true when 'false' then false end as tem_beneficios,
    nullif(url, '')              as url,
    nullif(faixa_posting, '')    as faixa_posting,
    try_cast(nullif(salario_min, '') as double) as salario_min,
    try_cast(nullif(salario_max, '') as double) as salario_max,
    nullif(salario_moeda, '')    as salario_moeda,
    nullif(salario_tipo, '')     as salario_tipo
from read_csv('{{ var("data_dir") }}/vagas.csv', header = true, all_varchar = true)
