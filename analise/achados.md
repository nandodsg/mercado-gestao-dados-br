# Achados: o que as vagas de gestão de dados pedem, coordenação × gerência

> Arquivo gerado por `analise/achados.py` a partir de `achados.modelo.md`. **Não edite o `.md` gerado**: os números saem
> dos marts do dbt e se refazem a cada publicação. Publicação usada nesta geração: 2026-11-11. Cobertura da
> classificação: 100% (2001 de 2001) linhas de anúncio.

**Antes de citar:** é a amostra de uma pessoa, não o mercado (ver "Vieses e limites" no README). Cada número traz o
tamanho da amostra ao lado. As porcentagens são de **vagas** (uma vaga conta uma vez por item, por mais linhas que o
citem), e a classificação tende a deixar de marcar item mais do que a marcar à toa: **trate as contagens como piso**.
Diferença entre níveis vem com o p do teste exato de Fisher. Com dezenas de itens comparados, a régua é esta: p abaixo
de 0,01 é diferença em que dá pra apoiar uma frase; entre 0,01 e 0,05 é direção, citada junto do achado do mesmo tema;
acima de 0,05 vai para o fim, em "O que os dados ainda não sustentam".

**Base.** 90 vagas publicadas, 83 com o anúncio classificado: **36 de coordenação e 42 de
gerência**, mais 5 de alta gestão ou fora da gestão de dados, que entram só nos totais. Ficam de fora
6 vagas cujo anúncio não chegou à classificação e 1 anúncio repetido (a mesma empresa publicando o mesmo texto
no mesmo nível conta uma vez).

---

## 1. O núcleo é gente e negócio, nos dois níveis

Três itens aparecem em quase toda vaga, e quase na mesma proporção em coordenação e gerência:

| item | coordenação | gerência |
|---|---|---|
| liderar o time | 92% (33 de 36) | 95% (40 de 42) |
| relacionamento com áreas de negócio (stakeholders) | 92% (33 de 36) | 86% (36 de 42) |
| desenvolver pessoas | 78% (28 de 36) | 86% (36 de 42) |

Nenhuma ferramenta aparece com essa frequência; a mais citada pelo nome, SQL, fica abaixo de todos os três
(seção 3). O que separa os níveis está no resto do anúncio.

## 2. Coordenação opera o time; gerência decide para onde ele vai

As duas maiores diferenças entre os níveis, e as duas únicas com força estatística folgada:

| item | coordenação | gerência | teste |
|---|---|---|---|
| estratégia e visão | 28% (10 de 36) | 71% (30 de 42) | p < 0,001 |
| operação do time (rotina, entregas, acompanhamento) | 72% (26 de 36) | 38% (16 de 42) | p = 0,003 |
| *na mesma direção, com menos força:* contratar e estruturar o time | 11% (4 de 36) | 33% (14 de 42) | p = 0,030 |

O anúncio de gerência descreve quem desenha a área; o de coordenação, quem faz ela rodar.

## 3. Python é pedido de coordenação

Ferramenta citada pelo nome em qualquer linha do anúncio (regra determinística, `dbt/seeds/ferramentas.csv`,
publicada na coluna `ferramentas` de `rotulos.csv`). A base é a das outras seções: 36 vagas de coordenação e 42 de
gerência com o anúncio classificado. Citar o nome é diferente de exigir a ferramenta (pode estar em diferencial ou numa
lista de exemplos), e quem não a nomeia pode pedi-la por outro termo: **trate como piso**.

| ferramenta | coordenação | gerência | teste |
|---|---|---|---|
| Python | 53% (19 de 36) | 21% (9 de 42) | p = 0,005 |
| SQL | 67% (24 de 36) | 48% (20 de 42) | p = 0,112 |
| AWS, Azure ou GCP (qualquer) | 31% (11 de 36) | 43% (18 de 42) | p = 0,348 |

Python é a única ferramenta em que os níveis se separam com folga. SQL e nuvem citada pelo nome não se separam do
acaso.

## 4. Metade pede mão na massa, nos dois níveis

**Mão na massa** (o gestor também executa, codifica, constrói) aparece em 47% (17 de 36) das vagas de coordenação e
em 50% (21 de 42) das de gerência (p = 0,824). Cerca de metade dos anúncios pede isso, e subir de nível não muda a conta.

## 5. IA já está na maioria das vagas, mais como tarefa do que como pré-requisito

Algum item de IA (ciência de dados e ML, IA aplicada ao negócio, IA generativa, agentes, MLOps, governança de
IA) aparece em 70% (58 de 83) das vagas: 61% (22 de 36) em coordenação e 76% (32 de 42) em gerência.

- Em 78% (45 de 58) dessas vagas a IA está na seção de **responsabilidades**, no que a pessoa vai fazer. Na de
  **requisitos**, no que ela já precisa saber, em 60% (35 de 58). (Uma vaga pode ter as duas.)
- Gerência cita mais IA. Na mesma direção, com menos força: **IA aplicada ao negócio**, 31% (11 de 36) em coordenação ×
  55% (23 de 42) em gerência (p = 0,040).
- É o **diferencial mais citado**: aparece em 67% (24 de 36) das vagas que têm seção de diferenciais, somando os dois
  níveis. O segundo é experiência no setor da empresa: 61% (22 de 36).

## 6. Nenhum anúncio diz quanto paga

**0 de 90** anúncios declaram faixa salarial. O que se sabe de salário vem de fora do anúncio:
376 referências de 40 sites (guias salariais, Glassdoor, Indeed e outros), pesquisadas vaga a
vaga.

| | coordenação | gerência |
|---|---|---|
| vagas com referência pesquisada | 36 | 41 |
| mediana do ponto médio da faixa de referência | R$ 16,6 mil | R$ 30,3 mil |
| vagas cuja referência é a mesma faixa de um guia salarial (a faixa mais repetida) | 11% (4 de 36) | 29% (12 de 41) |

**Isto não é o que as vagas pagam.** É a referência de mercado para o cargo e a cidade. Parte das fontes bloqueia
leitura automática e veio de resumo de busca, e a mesma faixa de um guia salarial se repete em muitas vagas (última
linha da tabela): a mediana da gerência, em especial, fica presa a ela.

---

## O que os dados ainda não sustentam

Diferenças que parecem grandes, mas que a amostra não separa do acaso. Servem para levantar pergunta, não para
afirmar:

| item | coordenação | gerência | teste |
|---|---|---|---|
| inglês | 22% (8 de 36) | 40% (17 de 42) | p = 0,096 |
| IA generativa e LLMs | 17% (6 de 36) | 36% (15 de 42) | p = 0,075 |
| KPIs e métricas | 75% (27 de 36) | 52% (22 de 42) | p = 0,060 |
| liderar líderes | 3% (1 de 36) | 17% (7 de 42) | p = 0,063 |
| plataforma de dados e nuvem (a responsabilidade pela plataforma, mesmo sem nome de fornecedor) | 47% (17 de 36) | 67% (28 de 42) | p = 0,109 |

Também fora daqui, de propósito: **localização, setor da empresa e tendência no tempo.** A distribuição geográfica e a
de setores refletem a busca do autor, não o mercado, e a janela de coleta ainda é curta para falar de tendência.
