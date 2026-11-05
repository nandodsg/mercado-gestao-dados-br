-- 1 linha por linha de requisito do posting (data/requisitos.csv), texto literal. A quebra em requisitos atômicos e a
-- classificação entram no pipeline do Item 7 e viram outra tabela; esta é a entrada crua.
select
    id_publico,
    try_cast(ordem as integer) as ordem,
    texto
from read_csv('{{ var("data_dir") }}/requisitos.csv', header = true, all_varchar = true)
