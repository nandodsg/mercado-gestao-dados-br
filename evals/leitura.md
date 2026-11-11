## Leitura e recomendação

**Recomendação: Claude Haiku 5.5 como modelo de produção do Item 7.** A escolha é do autor.

- **Qualidade.** Haiku lidera os candidatos em tudo que importa pra análise: F1 micro 0,85, kappa médio por dimensão 0,87,
  `natureza` 0,99, 60% das linhas com o conjunto de itens exato. O GPT mini vem depois (0,81), o Jev 1.14 e o gpt-oss-120b
  empatam atrás (0,69 e 0,70). Nenhum chega à régua dos três rotuladores de origem (0,89 a 0,96), que tinham vantagem.
- **Custo e velocidade não decidem.** US$ 0,13 a 1,16 por mil linhas nos modelos de texto e US$ 0,44 no Jev: rotular os
  anúncios todos custa centavos em qualquer um. O Jev é 3 vezes mais rápido (0,3 s por linha, contra ~1 s), o que só importa
  se a CI virar gargalo, e não é o caso numa execução semanal.
- **Viés de família.** Haiku concorda com Gemini e Grok (empresas que não escreveram a taxonomia) tanto quanto com o Opus
  (0,87 e 0,89 contra 0,88), e na mesma proporção do GPT mini: sem sinal de que a vantagem venha do parentesco.
- **Jev.** Com o limiar escolhido na prática (0,20 a 0,25, não 0,50) o F1 micro sobe de 0,51–0,53 pra 0,66–0,69, mas a
  precisão fica em 0,64–0,68: marca item demais. A abstenção funciona: nas decisões em que a probabilidade é firme (94% do
  total) o erro é de 0,3%; nas incertas, 38%. Isso abre um desenho híbrido (Jev decide o firme, o Haiku revê só as linhas
  com algum item incerto), que **não foi medido** aqui e só vale a pena se o volume crescer. O Jev também não escreve o
  `outro` nem justifica, o que pesa na auditoria da classificação.
- **Pontos fracos**: `analytics.marketing_cliente` é o pior item de todos (F1 de 0,18 e 0,28 no Jev, 0,37 no gpt-oss, 0,65 no GPT mini
  e no Haiku), seguido de `negocio.produto_dados` (0,33 a 0,70) e `pessoas.hands_on` (0,32 no Jev, 0,53 no gpt-oss, 0,80 no Haiku).
  O Item 7 deve revisar por amostra as linhas com esses itens, ou a regra de borda deles volta pra taxonomia numa versão nova
  (que muda a `versao` e pede nova rotulagem da referência).
