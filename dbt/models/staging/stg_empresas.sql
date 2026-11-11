-- 1 linha por empresa que aparece em vagas.csv (contrato v1, data/empresas.csv): grafia como sai de vagas.csv, nome
-- normalizado (grafias repetidas da mesma empresa viram uma) e setor de atuação, da lista fechada do seed `lista_setores`.
select
    empresa,
    empresa_normalizada,
    setor
from read_csv('{{ var("data_dir") }}/empresas.csv', header = true, all_varchar = true)
