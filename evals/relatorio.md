# Harness de modelos — candidatos × referência

Taxonomia `ed47eaa18707`, esforço `medium` nos modelos de texto, uma chamada por vaga (Jev: uma requisição por linha). Gabarito: 380 linhas de 16 vagas, rótulos de modelos revisados por pessoa (D25). Itens com 10+ positivas no gabarito (35) têm F1 próprio; o item `outro` (8 positivas) fica fora das métricas de item (o Jev não o pergunta).

## Resultado

| métrica | jev-1.13.0 | jev-1.14.0 | gpt-5.4-mini | gpt-oss-120b | claude-haiku-5.5 | claude-opus-5-5 | gemini-4-argon | grok-4.7 |
|---|---|---|---|---|---|---|---|---|
| vagas devolvidas válidas (de 16) | 16 | 16 | 16 | 16 | 16 | 16 | 16 | 16 |
| `natureza`: kappa | 0.90 | 0.90 | 0.99 | 0.95 | 0.99 | 1.00 | 0.99 | 1.00 |
| kappa da presença por dimensão (média das 8) | 0.66 | 0.69 | 0.83 | 0.77 | 0.87 | 0.94 | 0.96 | 0.88 |
| F1 por item (média dos itens avaliáveis) | 0.67 | 0.71 | 0.79 | 0.68 | 0.85 | 0.93 | 0.95 | 0.89 |
| F1 micro (linha × item) | 0.66 | 0.69 | 0.81 | 0.70 | 0.85 | 0.94 | 0.96 | 0.89 |
| precisão / revocação micro | 0.68 / 0.64 | 0.64 / 0.74 | 0.93 / 0.72 | 0.87 / 0.59 | 0.95 / 0.77 | 0.99 / 0.89 | 0.98 / 0.93 | 0.99 / 0.81 |
| conjunto exato de itens | 25% | 30% | 52% | 41% | 60% | 77% | 83% | 65% |
| setor (linhas com setor no gabarito) | 6/17 | 7/17 | 12/17 | 10/17 | 14/17 | 17/17 | 15/17 | 15/17 |
| US$ por 1.000 linhas | 0.44 | 0.44 | 1.16 | 0.13 | 0.17 | — | 1.47 | 3.46 |
| latência por linha, mediana (s) | 0.34 | 0.33 | 1.33 | 0.97 | 0.93 | n/d | n/d | n/d |
| reparos de forma | 0 | 0 | 1 | 6 | 2 | 0 | 0 | 0 |

Os três últimos (claude-opus-5-5, gemini-4-argon, grok-4.7) são a **régua**: rotularam a referência antes da revisão, então leem melhor do que leriam num conjunto novo. Latência dos modelos de texto = tempo da chamada da vaga ÷ linhas, uma de cada vez; a do Jev é por requisição (4 em paralelo).

## F1 por item (só os avaliáveis)

| item | positivas | jev-1.13.0 | jev-1.14.0 | gpt-5.4-mini | gpt-oss-120b | claude-haiku-5.5 | claude-opus-5-5 | gemini-4-argon | grok-4.7 |
|---|---|---|---|---|---|---|---|---|---|
| `pessoas.liderar_time` | 39 | 0.82 | 0.80 | 0.90 | 0.84 | 0.91 | 0.97 | 0.97 | 0.97 |
| `pessoas.multidisciplinar` | 10 | 0.69 | 0.65 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `pessoas.desenvolver_pessoas` | 19 | 0.97 | 1.00 | 0.97 | 0.94 | 0.97 | 0.95 | 0.97 | 0.95 |
| `pessoas.operacao_time` | 24 | 0.45 | 0.72 | 0.68 | 0.43 | 0.78 | 0.89 | 0.96 | 0.91 |
| `pessoas.hands_on` | 27 | 0.35 | 0.32 | 0.68 | 0.53 | 0.80 | 0.81 | 0.96 | 0.83 |
| `negocio.estrategia` | 13 | 0.46 | 0.39 | 0.84 | 0.74 | 0.77 | 0.96 | 1.00 | 0.87 |
| `negocio.roadmap_priorizacao` | 17 | 0.74 | 0.83 | 0.94 | 0.91 | 1.00 | 0.94 | 1.00 | 0.97 |
| `negocio.projetos_portfolio` | 26 | 0.50 | 0.67 | 0.80 | 0.65 | 0.82 | 0.88 | 0.96 | 0.83 |
| `negocio.stakeholders` | 39 | 0.78 | 0.83 | 0.79 | 0.62 | 0.82 | 0.92 | 0.95 | 0.89 |
| `negocio.comunicacao_executiva` | 15 | 0.81 | 0.89 | 0.80 | 0.81 | 0.93 | 0.97 | 0.93 | 0.97 |
| `negocio.visao_negocio` | 35 | 0.73 | 0.70 | 0.61 | 0.33 | 0.76 | 0.89 | 0.99 | 0.89 |
| `negocio.cultura_dados` | 12 | 0.67 | 0.80 | 0.80 | 0.83 | 0.91 | 0.96 | 0.92 | 0.87 |
| `negocio.transformacao_inovacao` | 10 | 1.00 | 0.87 | 0.71 | 0.50 | 0.95 | 1.00 | 0.95 | 0.95 |
| `negocio.produto_dados` | 15 | 0.33 | 0.48 | 0.64 | 0.64 | 0.70 | 0.90 | 0.93 | 0.93 |
| `negocio.clientes_consultoria` | 19 | 0.89 | 0.92 | 0.64 | 0.48 | 0.71 | 0.97 | 0.97 | 0.94 |
| `negocio.processos_melhoria` | 14 | 0.69 | 0.69 | 0.75 | 0.67 | 0.78 | 0.92 | 0.92 | 0.88 |
| `analytics.bi_dashboards` | 20 | 0.90 | 0.88 | 0.95 | 0.84 | 0.89 | 0.98 | 0.95 | 0.97 |
| `analytics.analise_insights` | 51 | 0.70 | 0.74 | 0.83 | 0.62 | 0.78 | 0.93 | 0.90 | 0.77 |
| `analytics.kpis_metricas` | 21 | 0.60 | 0.90 | 0.93 | 0.89 | 0.89 | 0.95 | 1.00 | 0.92 |
| `analytics.marketing_cliente` | 31 | 0.18 | 0.28 | 0.65 | 0.37 | 0.65 | 0.93 | 0.93 | 0.64 |
| `eng.arquitetura` | 18 | 0.88 | 0.88 | 0.88 | 0.65 | 0.88 | 0.94 | 0.97 | 0.88 |
| `eng.pipelines` | 18 | 0.86 | 0.84 | 0.80 | 0.71 | 0.88 | 0.91 | 1.00 | 0.91 |
| `eng.integracao` | 15 | 0.86 | 0.90 | 0.86 | 0.67 | 0.86 | 1.00 | 0.93 | 0.85 |
| `eng.plataforma_cloud` | 21 | 0.71 | 0.82 | 0.89 | 0.78 | 0.90 | 0.95 | 0.90 | 0.95 |
| `eng.boas_praticas` | 14 | 0.44 | 0.57 | 0.67 | 0.55 | 0.70 | 0.92 | 0.88 | 0.64 |
| `eng.observabilidade_operacao` | 17 | 0.30 | 0.62 | 0.67 | 0.62 | 0.85 | 0.97 | 1.00 | 0.79 |
| `eng.software_sistemas` | 13 | 0.56 | 0.53 | 0.38 | 0.13 | 0.56 | 0.63 | 0.89 | 0.63 |
| `gov.governanca` | 16 | 0.32 | 0.55 | 0.97 | 0.91 | 1.00 | 1.00 | 1.00 | 1.00 |
| `gov.qualidade` | 17 | 0.94 | 0.88 | 0.94 | 0.88 | 0.97 | 1.00 | 1.00 | 0.97 |
| `ia.ciencia_dados_ml` | 23 | 0.88 | 0.91 | 0.82 | 0.72 | 0.96 | 0.96 | 0.96 | 0.96 |
| `ia.ia_aplicada` | 13 | 0.83 | 0.67 | 0.92 | 0.67 | 0.92 | 1.00 | 0.92 | 1.00 |
| `formacao.graduacao` | 10 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `experiencia.dados` | 10 | 0.48 | 0.52 | 0.53 | 0.57 | 0.62 | 0.57 | 0.82 | 0.95 |
| `experiencia.setor` | 17 | 0.67 | 0.62 | 0.84 | 0.74 | 0.85 | 1.00 | 0.94 | 0.94 |
| `comportamento.comunicacao` | 13 | 0.34 | 0.36 | 0.69 | 0.53 | 0.87 | 0.92 | 1.00 | 0.82 |

## Kappa da presença por dimensão

| dimensão | jev-1.13.0 | jev-1.14.0 | gpt-5.4-mini | gpt-oss-120b | claude-haiku-5.5 | claude-opus-5-5 | gemini-4-argon | grok-4.7 |
|---|---|---|---|---|---|---|---|---|
| Gestão de pessoas | 0.39 | 0.39 | 0.80 | 0.72 | 0.86 | 0.90 | 0.96 | 0.91 |
| Estratégia, negócio e gestão | 0.77 | 0.85 | 0.81 | 0.79 | 0.85 | 0.91 | 0.97 | 0.90 |
| Analytics e BI | 0.69 | 0.74 | 0.83 | 0.73 | 0.81 | 0.93 | 0.94 | 0.81 |
| Engenharia e plataforma de dados | 0.70 | 0.80 | 0.84 | 0.77 | 0.88 | 0.93 | 0.95 | 0.84 |
| Governança, qualidade e segurança | 0.74 | 0.78 | 0.88 | 0.86 | 0.94 | 0.96 | 1.00 | 0.92 |
| IA e ciência de dados | 0.89 | 0.85 | 0.95 | 0.93 | 0.97 | 0.97 | 0.97 | 0.97 |
| Formação, idioma e experiência | 0.70 | 0.72 | 0.84 | 0.86 | 0.88 | 0.95 | 0.95 | 0.95 |
| Comportamental e condições | 0.41 | 0.38 | 0.73 | 0.50 | 0.80 | 0.95 | 0.95 | 0.78 |

## Jev: limiar e abstenção

O sim/não do Jev vira item quando a probabilidade passa do limiar. O limiar foi escolhido na **prática** (88 linhas, maximiza o F1 micro; gabarito dela foi revisado numa versão anterior da taxonomia), não na referência.

**typesafe/jev-1.13.0**: limiar escolhido 0.25; F1 micro na referência 0.66 (com 0,50: 0.51).

| faixa de probabilidade | decisões sim/não | erros | taxa de erro |
|---|---|---|---|
| firme (p ≤ 0,10 ou ≥ 0,90) | 23,801 | 84 | 0.4% |
| média (0,10–0,25 ou 0,75–0,90) | 954 | 226 | 23.7% |
| incerta (0,25–0,75) | 609 | 232 | 38.1% |

**typesafe/jev-1.14.0**: limiar escolhido 0.20; F1 micro na referência 0.69 (com 0,50: 0.53).

| faixa de probabilidade | decisões sim/não | erros | taxa de erro |
|---|---|---|---|
| firme (p ≤ 0,10 ou ≥ 0,90) | 23,872 | 66 | 0.3% |
| média (0,10–0,25 ou 0,75–0,90) | 921 | 273 | 29.6% |
| incerta (0,25–0,75) | 571 | 216 | 37.8% |


## Conferência de viés de família

O Opus escreveu a taxonomia e rotulou a referência. Pra ver se o Haiku (mesma empresa) se beneficia, o F1 micro de cada candidato de texto contra os rótulos **de cada rotulador original**, antes da revisão:

| candidato | × opus | × gemini | × grok |
|---|---|---|---|
| gpt-5.4-mini | 0.84 | 0.82 | 0.84 |
| gpt-oss-120b | 0.73 | 0.72 | 0.76 |
| claude-haiku-5.5 | 0.88 | 0.87 | 0.89 |

## Ressalvas

- A referência é "rótulos de modelos revisados por pessoa" (D25), não rotulagem cega dele: 34 das 877 decisões de item foram mudadas na revisão, o resto ele aceitou. Os três rotuladores de origem têm vantagem na régua.
- O Opus também escreveu a taxonomia; Haiku é da mesma empresa (ver a conferência acima).
- Os modelos de texto rodaram uma vez, esforço `medium`; o prompt é o do Item 5, sem ajuste por modelo. Jev: um único desenho de perguntas (definição, borda e exemplos do `taxonomia.md` por item), sem iteração; outro desenho pode render mais ou menos.
- Jev não devolve justificativa nem escreve o `outro`; benchmarks dele são do fornecedor e há quem conteste a categoria ([InfoWorld](https://www.infoworld.com/article/4236103/typesafes-jev-even-more-susceptible-to-attack-than-llms-says-security-vendor.html)).
- `peso`, `anos` e ferramentas saem por regra (`regras.py`), fora da disputa; o gabarito da referência não tem esses campos, então não foram medidos aqui.
- Latência e custo: uma rodada, uma máquina, rede doméstica; ordem de grandeza, não benchmark.

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
