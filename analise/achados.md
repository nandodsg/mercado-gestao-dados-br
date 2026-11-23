# Achados: o que as vagas de gestão de dados pedem, coordenação × gerência

> Arquivo gerado por `analise/achados.py` a partir de `achados.modelo.md`. **Não edite o `.md` gerado**: os números saem
> dos marts do dbt e se refazem a cada publicação. Publicação usada nesta geração: 2026-11-23. Cobertura da
> classificação: 100% (3026 de 3026) linhas de anúncio.

**Antes de citar:** é a amostra de uma pessoa, não o mercado (ver "Vieses e limites" no README). Cada número traz o
tamanho da amostra ao lado. As porcentagens são de **vagas** (uma vaga conta uma vez por item, por mais linhas que o
citem), e a classificação tende a deixar de marcar item mais do que a marcar à toa: **trate as contagens como piso**.
Diferença entre níveis vem com o p do teste exato de Fisher. Com dezenas de itens comparados, a régua é esta: p abaixo
de 0,01 é diferença em que dá pra apoiar uma frase; entre 0,01 e 0,05 é direção, citada junto do achado do mesmo tema;
acima de 0,05 vai para o fim, em "O que os dados ainda não sustentam".

**Base.** 130 vagas publicadas, 121 com o anúncio classificado: **53 de coordenação e 60 de
gerência**, mais 8 de alta gestão ou fora da gestão de dados, que entram só nos totais. Ficam de fora
8 vagas cujo anúncio não chegou à classificação e 1 anúncio repetido (a mesma empresa publicando o mesmo texto
no mesmo nível conta uma vez).

---

## 1. O núcleo é gente e negócio, nos dois níveis

> ⚠ **Não se sustenta nesta publicação**: a direção abaixo mudou com o dado novo; o texto espera revisão.

Três itens aparecem em quase toda vaga, e quase na mesma proporção em coordenação e gerência:

| item | coordenação | gerência |
|---|---|---|
| liderar o time | 89% (47 de 53) | 97% (58 de 60) |
| relacionamento com áreas de negócio (stakeholders) | 92% (49 de 53) | 87% (52 de 60) |
| desenvolver pessoas | 70% (37 de 53) | 77% (46 de 60) |

Nenhuma ferramenta aparece com essa frequência; a mais citada pelo nome, SQL, fica abaixo de todos os três
(seção 3). O que separa os níveis está no resto do anúncio.

## 2. Coordenação opera o time; gerência decide para onde ele vai

As duas maiores diferenças entre os níveis, e as duas únicas com força estatística folgada:

| item | coordenação | gerência | teste |
|---|---|---|---|
| estratégia e visão | 25% (13 de 53) | 65% (39 de 60) | p < 0,001 |
| operação do time (rotina, entregas, acompanhamento) | 70% (37 de 53) | 38% (23 de 60) | p = 0,001 |
| *na mesma direção, com menos força:* contratar e estruturar o time | 9% (5 de 53) | 28% (17 de 60) | p = 0,016 |

O anúncio de gerência descreve quem desenha a área; o de coordenação, quem faz ela rodar.

## 3. Python é pedido de coordenação

Ferramenta citada pelo nome em qualquer linha do anúncio (regra determinística, `dbt/seeds/ferramentas.csv`,
publicada na coluna `ferramentas` de `rotulos.csv`). A base é a das outras seções: 53 vagas de coordenação e 60 de
gerência com o anúncio classificado. Citar o nome é diferente de exigir a ferramenta (pode estar em diferencial ou numa
lista de exemplos), e quem não a nomeia pode pedi-la por outro termo: **trate como piso**.

| ferramenta | coordenação | gerência | teste |
|---|---|---|---|
| Python | 49% (26 de 53) | 28% (17 de 60) | p = 0,033 |
| SQL | 64% (34 de 53) | 48% (29 de 60) | p = 0,129 |
| AWS, Azure ou GCP (qualquer) | 28% (15 de 53) | 40% (24 de 60) | p = 0,236 |

Python é a única ferramenta em que os níveis se separam com folga. SQL e nuvem citada pelo nome não se separam do
acaso.

## 4. Metade pede mão na massa, nos dois níveis

**Mão na massa** (o gestor também executa, codifica, constrói) aparece em 47% (25 de 53) das vagas de coordenação e
em 47% (28 de 60) das de gerência (p = 1,000). Cerca de metade dos anúncios pede isso, e subir de nível não muda a conta.

## 5. IA já está na maioria das vagas, mais como tarefa do que como pré-requisito

Algum item de IA (ciência de dados e ML, IA aplicada ao negócio, IA generativa, agentes, MLOps, governança de
IA) aparece em 68% (82 de 121) das vagas: 57% (30 de 53) em coordenação e 75% (45 de 60) em gerência.

- Em 73% (60 de 82) dessas vagas a IA está na seção de **responsabilidades**, no que a pessoa vai fazer. Na de
  **requisitos**, no que ela já precisa saber, em 60% (49 de 82). (Uma vaga pode ter as duas.)
- Gerência cita mais IA. Na mesma direção, com menos força: **IA aplicada ao negócio**, 32% (17 de 53) em coordenação ×
  55% (33 de 60) em gerência (p = 0,022).
- É o **diferencial mais citado**: aparece em 60% (34 de 57) das vagas que têm seção de diferenciais, somando os dois
  níveis. O segundo é experiência no setor da empresa: 58% (33 de 57).

## 6. Nenhum anúncio diz quanto paga

**0 de 130** anúncios declaram faixa salarial. O que se sabe de salário vem de fora do anúncio:
517 referências de 51 sites (guias salariais, Glassdoor, Indeed e outros), pesquisadas vaga a
vaga.

| | coordenação | gerência |
|---|---|---|
| vagas com referência pesquisada | 45 | 56 |
| mediana do ponto médio da faixa de referência | R$ 16,6 mil | R$ 29,4 mil |
| vagas cuja referência é a mesma faixa de um guia salarial (a faixa mais repetida) | 9% (4 de 45) | 21% (12 de 56) |

**Isto não é o que as vagas pagam.** É a referência de mercado para o cargo e a cidade. Parte das fontes bloqueia
leitura automática e veio de resumo de busca, e a mesma faixa de um guia salarial se repete em muitas vagas (última
linha da tabela): a mediana da gerência, em especial, fica presa a ela.

---

## O que os dados ainda não sustentam

Diferenças que parecem grandes, mas que a amostra não separa do acaso. Servem para levantar pergunta, não para
afirmar:

| item | coordenação | gerência | teste |
|---|---|---|---|
| inglês | 19% (10 de 53) | 43% (26 de 60) | p = 0,008 |
| IA generativa e LLMs | 11% (6 de 53) | 33% (20 de 60) | p = 0,007 |
| KPIs e métricas | 70% (37 de 53) | 57% (34 de 60) | p = 0,175 |
| liderar líderes | 2% (1 de 53) | 13% (8 de 60) | p = 0,035 |
| plataforma de dados e nuvem (a responsabilidade pela plataforma, mesmo sem nome de fornecedor) | 45% (24 de 53) | 63% (38 de 60) | p = 0,061 |

Também fora daqui, de propósito: **localização, setor da empresa e tendência no tempo.** A distribuição geográfica e a
de setores refletem a busca do autor, não o mercado, e a janela de coleta ainda é curta para falar de tendência.
