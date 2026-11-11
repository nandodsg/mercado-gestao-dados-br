# Achados: o que as vagas de gestão de dados pedem, coordenação × gerência

> Arquivo gerado por `analise/achados.py` a partir de `achados.modelo.md`. **Não edite o `.md` gerado**: os números saem
> dos marts do dbt e se refazem a cada publicação. Publicação usada nesta geração: {versao_dado}. Cobertura da
> classificação: {cobertura} linhas de anúncio.

**Antes de citar:** é a amostra de uma pessoa, não o mercado (ver "Vieses e limites" no README). Cada número traz o
tamanho da amostra ao lado. As porcentagens são de **vagas** (uma vaga conta uma vez por item, por mais linhas que o
citem), e a classificação tende a deixar de marcar item mais do que a marcar à toa: **trate as contagens como piso**.
Diferença entre níveis vem com o p do teste exato de Fisher. Com dezenas de itens comparados, a régua é esta: p abaixo
de 0,01 é diferença em que dá pra apoiar uma frase; entre 0,01 e 0,05 é direção, citada junto do achado do mesmo tema;
acima de 0,05 vai para o fim, em "O que os dados ainda não sustentam".

**Base.** {n_vagas} vagas publicadas, {n_rotuladas} com o anúncio classificado: **{nc} de coordenação e {ng} de
gerência**, mais {n_outros_niveis} de alta gestão ou fora da gestão de dados, que entram só nos totais. Ficam de fora
{n_sem_rotulo} vagas cujo anúncio não chegou à classificação e {repost_txt} (a mesma empresa publicando o mesmo texto
no mesmo nível conta uma vez).

---

## 1. O núcleo é gente e negócio, nos dois níveis

{aviso_c1}Três itens aparecem em quase toda vaga, e quase na mesma proporção em coordenação e gerência:

| item | coordenação | gerência |
|---|---|---|
| liderar o time | {liderar_c} | {liderar_g} |
| relacionamento com áreas de negócio (stakeholders) | {stake_c} | {stake_g} |
| desenvolver pessoas | {desenv_c} | {desenv_g} |

Nenhuma ferramenta aparece com essa frequência; a mais citada pelo nome, {ferr_top}, fica abaixo de todos os três
(seção 3). O que separa os níveis está no resto do anúncio.

## 2. Coordenação opera o time; gerência decide para onde ele vai

{aviso_c2}As duas maiores diferenças entre os níveis, e as duas únicas com força estatística folgada:

| item | coordenação | gerência | teste |
|---|---|---|---|
| estratégia e visão | {estrat_c} | {estrat_g} | {estrat_p} |
| operação do time (rotina, entregas, acompanhamento) | {oper_c} | {oper_g} | {oper_p} |
| *na mesma direção, com menos força:* contratar e estruturar o time | {contratar_c} | {contratar_g} | {contratar_p} |

O anúncio de gerência descreve quem desenha a área; o de coordenação, quem faz ela rodar.

## 3. Python é pedido de coordenação

{aviso_c3}Ferramenta citada pelo nome (regra determinística, `dbt/seeds/ferramentas.csv`) na lista de requisitos de
`requisitos.csv`; {rc} vagas de coordenação e {rg} de gerência têm essa lista. A lista é um resumo do anúncio, não o
anúncio inteiro (ver o README): a base não é a mesma das outras seções e a contagem é piso.

| ferramenta | coordenação | gerência | teste |
|---|---|---|---|
| Python | {py_c} | {py_g} | {py_p} |
| SQL | {sql_c} | {sql_g} | {sql_p} |
| AWS, Azure ou GCP (qualquer) | {nuvem_c} | {nuvem_g} | {nuvem_p} |

Python é a única ferramenta em que os níveis se separam com folga. SQL e nuvem citada pelo nome não se separam do
acaso.

## 4. Metade pede mão na massa, nos dois níveis

{aviso_c4}**Mão na massa** (o gestor também executa, codifica, constrói) aparece em {hands_c} das vagas de coordenação e
em {hands_g} das de gerência ({hands_p}). Cerca de metade dos anúncios pede isso, e subir de nível não muda a conta.

## 5. IA já está na maioria das vagas, mais como tarefa do que como pré-requisito

{aviso_c5}Algum item de IA (ciência de dados e ML, IA aplicada ao negócio, IA generativa, agentes, MLOps, governança de
IA) aparece em {ia_tot} das vagas: {ia_c} em coordenação e {ia_g} em gerência.

- Em {ia_resp} dessas vagas a IA está na seção de **responsabilidades**, no que a pessoa vai fazer. Na de
  **requisitos**, no que ela já precisa saber, em {ia_req}. (Uma vaga pode ter as duas.)
- Gerência cita mais IA. Na mesma direção, com menos força: **IA aplicada ao negócio**, {iaap_c} em coordenação ×
  {iaap_g} em gerência ({iaap_p}).
- É o **diferencial mais citado**: aparece em {ia_dif} das vagas que têm seção de diferenciais, somando os dois
  níveis. O segundo é experiência no setor da empresa: {setor_dif}.

## 6. Nenhum anúncio diz quanto paga

{aviso_c6}**{n_faixa} de {n_vagas}** anúncios declaram faixa salarial. O que se sabe de salário vem de fora do anúncio:
{bench_fontes} referências de {bench_dominios} sites (guias salariais, Glassdoor, Indeed e outros), pesquisadas vaga a
vaga.

| | coordenação | gerência |
|---|---|---|
| vagas com referência pesquisada | {sal_n_c} | {sal_n_g} |
| mediana do ponto médio da faixa de referência | {sal_med_c} | {sal_med_g} |
| vagas cuja referência é a mesma faixa de um guia salarial (a faixa mais repetida) | {sal_rep_c} | {sal_rep_g} |

**Isto não é o que as vagas pagam.** É a referência de mercado para o cargo e a cidade. Parte das fontes bloqueia
leitura automática e veio de resumo de busca, e a mesma faixa de um guia salarial se repete em muitas vagas (última
linha da tabela): a mediana da gerência, em especial, fica presa a ela.

---

## O que os dados ainda não sustentam

Diferenças que parecem grandes, mas que a amostra não separa do acaso. Servem para levantar pergunta, não para
afirmar:

| item | coordenação | gerência | teste |
|---|---|---|---|
| inglês | {ingles_c} | {ingles_g} | {ingles_p} |
| IA generativa e LLMs | {genai_c} | {genai_g} | {genai_p} |
| KPIs e métricas | {kpis_c} | {kpis_g} | {kpis_p} |
| liderar líderes | {lidlid_c} | {lidlid_g} | {lidlid_p} |
| plataforma de dados e nuvem (a responsabilidade pela plataforma, mesmo sem nome de fornecedor) | {cloud_c} | {cloud_g} | {cloud_p} |

Também fora daqui, de propósito: **localização, setor da empresa e tendência no tempo.** A distribuição geográfica e a
de setores refletem a busca do autor, não o mercado, e a janela de coleta ainda é curta para falar de tendência.
