Você rotula as linhas de requisito de uma vaga de liderança em dados, para uma análise de quais práticas, competências e
exigências os anúncios pedem. Você recebe **uma vaga inteira**: todas as linhas de requisito, na ordem em que aparecem,
numeradas. Algumas linhas continuam a anterior (começam com "…" ou parecem a segunda metade de uma frase): leia a vaga
toda antes de rotular.

Você não sabe a empresa nem o cargo, e isso é de propósito: rotule só pelo que cada linha escreve.

Para **cada linha**, devolva:

- `natureza`: `responsabilidade`, `requisito` ou `contexto`, como definido abaixo.
- `itens`: a lista de chaves de item da taxonomia que a linha **cita** (zero, um ou vários). Linha de natureza
  `contexto` fica com a lista vazia. Use `outro` só quando nenhum item cabe.
- `outro`: se `outro` está em `itens`, 3 a 6 palavras dizendo do que se trata; senão, texto vazio.
- `setor`: se `experiencia.setor` está em `itens`, o setor pedido, escolhido da lista de setores abaixo; senão,
  `nenhum`.
- `motivo`: uma frase curta (no máximo 25 palavras) dizendo o que na linha decidiu os itens. Cite no máximo poucas
  palavras da linha.

Regras: use a taxonomia exatamente como escrita, com as regras de borda de cada item. Ferramenta citada pelo nome
(SQL, Power BI, Python…) **não** é rotulada por você: outra etapa marca. Rotule o conceito ao redor. Peso (obrigatório ou
diferencial) e anos também não são seus.

<setores>
{setores}
</setores>

<taxonomia>
{taxonomia}
</taxonomia>
