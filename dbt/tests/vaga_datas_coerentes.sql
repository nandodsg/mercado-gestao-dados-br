-- A ordem natural das datas de uma vaga: publicada ≤ capturada ≤ lida linha a linha. Aviso, não erro: o anúncio pode trazer
-- uma data republicada, e a leitura de uma vaga antiga pode ter sido refeita depois. Tolera 2 dias entre a publicação e a captura
-- (as vagas dos primeiros meses foram registradas com um dia de folga de fuso). Linha devolvida = data fora de ordem.
{{ config(severity='warn') }}
select id_publico, data_publicacao, data_captura, data_analise
from {{ ref('stg_vagas') }}
where (data_publicacao is not null and data_publicacao > data_captura + 2)
   or data_captura > data_analise
