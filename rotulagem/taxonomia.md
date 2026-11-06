# Taxonomia de requisitos

Lista fechada de itens que o rotulador (modelo ou pessoa) usa pra dizer o que cada **linha de requisito** das vagas pede.
É a fonte única: os prompts leem este arquivo, o seed `dbt/seeds/taxonomia.csv` é gerado dele por
`rotulagem/gerar_seeds.py`, e a página de revisão mostra as mesmas definições. A versão da taxonomia é o hash deste
arquivo (`python rotulagem/taxonomia.py`) e vai em toda linha rotulada.

Os requisitos vêm dos postings, na ordem em que aparecem; uma vaga é rotulada inteira numa chamada, porque algumas linhas
continuam a anterior.

## Como o rotulador julga (vale pra cada modelo e pra pessoa que desempata)

1. **Uma linha pode ter vários itens.** Marcar todo item que a linha **cita**, nenhum que ela só sugere. "Liderar e
   desenvolver a equipe de BI, distribuindo demandas" = liderar time + desenvolver pessoas + operação do time. O
   **nome do time** ("equipe de BI", "time de engenharia de dados") não marca a prática: diz o recorte da vaga, não o
   que a linha pede. "Evoluir dashboards e indicadores" marca BI.
2. **Pelo que está escrito, nunca pela empresa ou pelo cargo.** Vaga de banco que não pede experiência no setor não
   ganha "experiência setorial: financeiro".
3. **Ferramenta citada pelo nome não é rotulada pelo modelo**: o dicionário (seção "Ferramentas") marca. O modelo marca
   o conceito ao redor: "SQL avançado, com modelagem em data warehouse colunar (Redshift, BigQuery, Snowflake)" →
   modelagem de dados + arquitetura de dados; SQL, Redshift, BigQuery e Snowflake vêm do dicionário. "Ferramentas de
   BI" sem nome → BI, dashboards e relatórios.
4. **Requisito partido em várias linhas** ("parte 1 / parte 2", "mesmo requisito", "…" no começo): cada pedaço recebe o
   que ele cita. A análise conta **vaga × item** (a vaga pede ou não pede), então pedaço repetido não infla.
5. **"Outro"** só quando nenhum item cabe; o rotulador escreve 3–6 palavras dizendo o que é (vira candidato a item novo
   na próxima versão).

## Rótulos por linha (além dos itens)

| rótulo | níveis | quem rotula | regra |
|---|---|---|---|
| `natureza` | **responsabilidade** · **requisito** · **contexto** | modelo | responsabilidade = o que a pessoa vai fazer ("Liderar a estratégia de dados"); requisito = o que ela precisa ter ou saber ("SQL avançado", "5 anos liderando times"); contexto = a linha não pede nada (nota, descrição da empresa ou do projeto: "contexto: migração de Teradata para Databricks", "Setor: varejo de moda, 145 anos"). Linha `contexto` sai da análise |
| `peso` | **obrigatório** · **diferencial** | regra | diferencial se a linha traz marcador: "Dif.", "Diferencial", "desejável", "nice (to have)", "great-to-have", "plus", "preferred", "será considerado um diferencial", "destaque" / "Dest.". Sem marcador = obrigatório. "Preferencialmente X" dentro de um requisito **não** vira diferencial (é preferência dentro de algo pedido). |
| `anos` | número ou vazio | regra | menor número de anos citado na linha ("5 e 10 anos" → 5; "8 anos na área… 3 em gestão formal" → 8 e 3 em itens diferentes: ver item "tempo de experiência") |

## Itens

### Gestão de pessoas

| item | chave | definição | borda | exemplos reais |
|---|---|---|---|---|
| Liderar time | `pessoas.liderar_time` | liderar, gerir ou coordenar um time ou uma área com gente | "liderar projetos" sem time não conta (vai em gestão de projetos); "liderança técnica sem gestão formal" conta, e marca também "referência técnica / hands-on" | "Liderar e orientar a equipe de engenharia de dados…"; "Experiência mínima de três anos com liderança de equipes" |
| Time multidisciplinar | `pessoas.multidisciplinar` | o time ou a liderança junta perfis diferentes (engenharia + ciência + BI, POs + devs) | só quando a linha diz que é misto; "time de dados" sozinho não | "Gerenciar times multidisciplinares … engenharia de dados, BI, analytics avançado e IA"; "Lead cross-functional teams, including data scientists, engineers…" |
| Desenvolver pessoas | `pessoas.desenvolver_pessoas` | PDI, feedback, 1:1, mentoria, coaching, avaliação de desempenho, carreira, capacitação do time | "desenvolver soluções" não é desenvolver pessoas | "Capacidade de realizar feedbacks estruturados, PDIs e avaliações de desempenho"; "Mentor, recruit, and retain top-tier … talent" |
| Contratar e estruturar time | `pessoas.contratar_estruturar` | recrutar, dimensionar headcount, montar ou crescer um time ou uma área | "estruturar processos" não conta | "Participar ativamente dos processos de recrutamento e seleção para expandir o time"; "Dimensionar estrutura e capacidade dos times…" |
| Liderar líderes | `pessoas.liderar_lideres` | gerir quem também lidera (coordenações, tech leads, líderes técnicos), formar lideranças | — | "gestão de times técnicos, incluindo liderança de líderes técnicos"; "desenvolvimento de lideranças intermediárias (Coordenações)" |
| Operação do time | `pessoas.operacao_time` | capacidade, alocação, rituais, distribuição de demandas, acompanhamento de entregas, remover impedimentos | priorização da área/roadmap vai em "roadmap e priorização" | "Gerir a capacidade e a alocação do time, removendo impedimentos…"; "Liderar e desenvolver a equipe de dados, distribuindo demandas e acompanhando entregas" |
| Referência técnica / hands-on | `pessoas.hands_on` | a liderança precisa pôr a mão, revisar código, tomar ou guiar decisão técnica, ser referência técnica | "base técnica para dialogar, não precisa construir" conta (é profundidade técnica pedida da liderança) | "Capacidade técnica para avaliar código SQL… com profundidade"; "Experiência prática (não apenas gestão…) em Analytics, Engenharia de Dados" |

### Estratégia, negócio e gestão

| item | chave | definição | borda | exemplos reais |
|---|---|---|---|---|
| Estratégia e visão | `negocio.estrategia` | definir ou executar estratégia/visão de dados, IA ou BI; pensamento estratégico | "alinhado aos objetivos estratégicos" sozinho não conta | "Desenvolver e executar a estratégia de dados da Cooperativa"; "Strong strategic thinking and product mindset" |
| Roadmap e priorização | `negocio.roadmap_priorizacao` | roadmap, backlog, priorização de demandas e iniciativas por valor | — | "Definir prioridades, roadmap e indicadores da área"; "Experience with value-based prioritization" |
| Projetos e portfólio | `negocio.projetos_portfolio` | gestão de projetos, cronograma, portfólio de iniciativas, condução de várias frentes | — | "Histórico em gestão de projetos complexos com múltiplas frentes de trabalho"; "gestão de portfólio de projetos e relacionamento com áreas de negócio" |
| Stakeholders e influência | `negocio.stakeholders` | parceria com áreas, influenciar sem autoridade, negociar escopo e prioridade, articulação entre áreas | apresentação pra diretoria vai em "comunicação executiva" | "Capacidade de influenciar stakeholders e conduzir iniciativas de transformação…"; "Atuar com Comercial, Jurídico, FP&A, Marketing e Tecnologia" |
| Comunicação executiva | `negocio.comunicacao_executiva` | apresentar pra diretoria, C-level, conselho, fóruns executivos; storytelling com dados | comunicação em geral vai em "comunicação" (comportamental) | "Comunicação executiva, com experiência apresentando para C-level e conselho"; "Conduzir apresentações executivas para stakeholders locais, regionais e globais" |
| Visão de negócio | `negocio.visao_negocio` | traduzir necessidade de negócio em solução, ligar dado a impacto/valor/ROI, business acumen, business case | — | "Conectar decisões técnicas ao impacto de negócio…"; "Construir business case, análises profundas e criar cenários" |
| Orçamento e fornecedores | `negocio.orcamento_fornecedores` | orçamento da área, OPEX/CAPEX, contratos, licenças, fornecedores, parceiros e consultorias contratadas | custo de nuvem/infra vai em FinOps | "Gestão de Orçamento, Contratos e Licenças…"; "Gerenciar fornecedores, consultorias, integradores e parceiros estratégicos…" |
| FinOps e custo de plataforma | `negocio.finops` | custo de nuvem, compute, ML ou inferência; otimização de custo da plataforma | — | "Promover a otimização contínua de custos de infraestrutura e processamento (FinOps)"; "Gerir o orçamento de compute e ferramentas de Machine Learning…" |
| Cultura de dados e adoção | `negocio.cultura_dados` | cultura data-driven, letramento, democratizar acesso, self-service, adoção pelas áreas | — | "Promover a cultura data-driven e o letramento em dados na organização…"; "democratizar o acesso à informação" |
| Transformação e inovação | `negocio.transformacao_inovacao` | transformação digital, inovação, PoC/MVP, prospectar tecnologias | migração de plataforma legada vai em "migração e modernização" | "Histórico de atuação em projetos de inovação e transformação digital"; "Prospectar tecnologias e tendências, conduzir provas de conceito e MVPs…" |
| Métodos ágeis | `negocio.ageis` | Scrum, Kanban, Lean, metodologias ágeis | — | "Conhecimento de metodologias ágeis, como Scrum, Kanban ou similares"; "Métodos ágeis e de inovação: Scrum/Kanban, Lean Portfolio…" |
| Produto e data products | `negocio.produto_dados` | gestão de produto, mentalidade de produto, data products, ciclo de vida de produtos de dados, discovery | — | "Oversee the entire lifecycle of data products…"; "Liderar a transição … para um modelo orientado a data products" |
| Clientes e consultoria | `negocio.clientes_consultoria` | atender clientes externos, perfil consultivo, prospecção, desenvolvimento de negócios, propostas | "clientes internos" não conta | "Experiência em consultoria ou atuação direta com clientes corporativos de grande porte"; "Vivência em prospecção, captura de oportunidades e desenvolvimento de negócios" |
| Processos e melhoria contínua | `negocio.processos_melhoria` | redesenho de processos, padronização, melhoria contínua | padronizar **métricas** vai em "KPIs e métricas" | "Promover o redesenho e a melhoria contínua dos processos corporativos"; "Histórico comprovado de padronização e melhoria de processos…" |

### Analytics e BI

| item | chave | definição | borda | exemplos reais |
|---|---|---|---|---|
| BI, dashboards e relatórios | `analytics.bi_dashboards` | construir ou evoluir BI, painéis, relatórios, visualização | "time de BI" sozinho não marca (regra 1) | "Supervisionar a criação, evolução e governança de dashboards executivos e operacionais…"; "Experiência com ferramentas de BI e visualização de dados" |
| Análise e insights | `analytics.analise_insights` | análises (exploratórias, diagnósticas, ad hoc), transformar dado em insight e recomendação | — | "Conduzir análises exploratórias e diagnósticas para apoiar a tomada de decisão"; "Transformar dados complexos em análises e recomendações…" |
| KPIs e métricas | `analytics.kpis_metricas` | definir, padronizar e acompanhar KPIs, métricas, OKRs, BSC | métricas de modelo (erro, drift) vão em ciência de dados / MLOps | "Definir e evoluir padrões de métricas, KPIs e conceitos analíticos…"; "Gestão de indicadores, BSC e OKRs" |
| Experimentação e causalidade | `analytics.experimentacao` | testes A/B, desenho de experimento, inferência causal, uplift, incrementalidade | — | "Base estatística sólida: desenho de experimentos, testes A/B e inferência causal"; "Experiência com inferência causal aplicada a decisões…" |
| Digital analytics e tagueamento | `analytics.digital_analytics` | web/product analytics, tracking, tagueamento, arquitetura de eventos | o nome GA/GTM vem do dicionário | "Digital Analytics em escala (GA, arquitetura de eventos)"; "Product Analytics / governança de tracking" |
| Analytics de marketing e cliente | `analytics.marketing_cliente` | MMM, atribuição, segmentação, CRM analytics, ciclo de vida, churn, LTV, insights de consumidor | — | "Marketing Measurement (MMM, atribuição, incrementality)"; "segmentações e clusters de clientes" |
| Inteligência comercial e de mercado | `analytics.inteligencia_mercado` | inteligência comercial, pesquisa e inteligência de mercado, pricing, benchmarking de concorrência | — | "Construir e manter a inteligência de mercado: benchmarking de concorrentes…"; "3+ years Consumer Insights or Market Research experience" |
| Planejamento financeiro e P&L | `analytics.financeiro_pl` | FP&A, orçamento e forecast do negócio, P&L, rentabilidade, finanças corporativas | orçamento **da área de dados** vai em "orçamento e fornecedores" | "análises de performance, rentabilidade e P&L"; "Conhecimento sólido em finanças corporativas e contabilidade gerencial" |
| Automação | `analytics.automacao` | automação de relatórios e processos, RPA, workflows | automação **com IA** marca também o item de IA | "Liderar iniciativas de automação de … RPAs"; "automação de relatórios e processos analíticos — intermediário" |

### Engenharia e plataforma de dados

| item | chave | definição | borda | exemplos reais |
|---|---|---|---|---|
| Arquitetura de dados | `eng.arquitetura` | arquitetura de dados; DW, data lake, lakehouse, data mesh, medalhão | — | "Domínio de Data Mesh"; "Vivência sólida em arquitetura de dados, incluindo data lake, data warehouse…" |
| Engenharia de dados e pipelines | `eng.pipelines` | pipelines, ETL/ELT, ingestão, orquestração, engenharia de dados como disciplina | "time de engenharia de dados" sozinho marca só liderar time | "Experiência com pipelines de dados (ETL/ELT) e ferramentas como…"; "Monitorar e controlar a execução de malhas de dados (pipelines)…" |
| Modelagem de dados | `eng.modelagem` | modelagem dimensional, analítica, corporativa; data vault; analytics engineering | modelagem **estatística/preditiva** vai em ciência de dados | "Data modeling (dimensional, Data Vault, semantic layers)"; "Experiência com modelagem analítica e transformação de dados em dbt…" |
| Integração de fontes e sistemas | `eng.integracao` | integrar múltiplas fontes, sistemas, APIs, conectores | — | "Integrar diferentes fontes de dados em um modelo corporativo consistente"; "Atuar na integração entre plataformas SCADA, sistemas de telemetria, BI, GIS…" |
| Plataforma de dados e nuvem | `eng.plataforma_cloud` | evoluir ou sustentar a plataforma de dados; nuvem como conceito | o provedor (AWS, Azure, GCP) vem do dicionário | "conduzir a evolução da nossa plataforma de dados"; "Familiaridade com Cloud (AWS, Azure ou GCP) e com os desafios de operar plataformas…" |
| Big data e processamento distribuído | `eng.big_data` | grandes volumes, processamento distribuído, larga escala | — | "Vivência com grandes volumes de dados"; "ambientes de processamento distribuído e plataformas de dados…" |
| Streaming e tempo real | `eng.streaming` | streaming, tempo real, baixa latência | — | "camadas de consumo NRT/Streaming Analytics (ex: Kafka, Pub/Sub)"; "ingestão batch e streaming de múltiplas fontes" |
| Boas práticas de engenharia (DevOps/DataOps) | `eng.boas_praticas` | versionamento, Git, CI/CD, testes, code review, documentação, DataOps | — | "Práticas modernas de engenharia: versionamento, testes automatizados, observabilidade e documentação"; "DataOps, CI/CD, Git, code review, testes e documentação" |
| Observabilidade e operação | `eng.observabilidade_operacao` | monitoramento, SLA/SLO, incidentes, sustentação, confiabilidade e disponibilidade da plataforma | qualidade **do dado** vai em "qualidade de dados" | "SLA, SLI e SLO… incidentes"; "Responder pela confiabilidade da plataforma analítica: monitoramento de pipelines…" |
| Migração e modernização | `eng.migracao_modernizacao` | migrar ou modernizar plataforma ou arquitetura legada | — | "Liderança comprovada de migrações de dados legados para ecossistemas modernos em nuvem"; "Vivência na condução de migrações de dados, modernização de plataformas analíticas…" |
| Camada semântica | `eng.camada_semantica` | camada semântica, métricas governadas como produto, data contracts | — | "Familiaridade com camadas semânticas e preparação de dados para consumo por LLM / text-to-SQL"; "Diferencial: camada semântica corporativa" |
| Software e sistemas (fora de dados) | `eng.software_sistemas` | desenvolvimento de software, arquitetura de software, sistemas como ERP/WMS/CRM, front/back-end | — | "Experiência sólida liderando times de desenvolvimento de software"; "Experiência em implantação ou transformação de plataformas como ERP, WMS, CRM…" |

### Governança, qualidade e segurança

| item | chave | definição | borda | exemplos reais |
|---|---|---|---|---|
| Governança de dados | `gov.governanca` | políticas, papéis (owners, stewards), padrões, frameworks (DAMA), programa de governança | "governança de modelos/IA" vai no item próprio | "Implantar e sustentar a governança de dados: papéis e responsabilidades…"; "Governança e qualidade de dados (DAMA-DMBOK)" |
| Qualidade de dados | `gov.qualidade` | qualidade, consistência, integridade, acuracidade do dado | — | "Conhecimento em modelagem de dados, qualidade de dados e governança"; "Implantar rotinas de validação e consistência dos dados antes de cada entrega…" |
| Catálogo, metadados e linhagem | `gov.catalogo_linhagem` | catálogo de dados, metadados, linhagem, dicionário de dados/métricas | — | "Data Quality, Metadata Management, Data Catalog, Data Lineage e Data Stewardship"; "Metadata and lineage management" |
| Dados mestres (MDM) | `gov.mdm` | master data management | — | "gestão de dados mestres (MDM) e práticas de governança"; "… e Master Data Management (MDM)" |
| Privacidade e regulação | `gov.privacidade_regulacao` | LGPD, privacidade, PII, compliance, regulação setorial (SOX, HIPAA) | — | "Conformidade com a LGPD, incluindo classificação, retenção e tratamento de dados pessoais"; "Governança de dados financeiros, incluindo SOX" |
| Segurança da informação e acesso | `gov.seguranca` | segurança da informação, controle de acesso | — | "governança e Segurança da Informação"; "Conhecimento prático de governança, privacidade e segurança de dados" |
| Governança de IA e de modelos | `gov.governanca_ia` | governança de modelos e agentes, risco de modelo, IA responsável, guardrails, ética de uso | — | "definir processos de governança de modelos + gestão de risco de modelos"; "Atuar como Centro de Excelência (CoE) na governança de agentes de IA…" |

### IA e ciência de dados

| item | chave | definição | borda | exemplos reais |
|---|---|---|---|---|
| IA generativa e LLMs | `ia.genai_llm` | GenAI, LLMs, RAG, embeddings, bancos vetoriais, dados preparados pra IA | — | "Vivência com Inteligência Artificial Generativa e utilização de LLMs"; "embeddings, Vector DBs (ex: Pinecone, Qdrant, ChromaDB) ou RAG" |
| Agentes de IA | `ia.agentes` | agentes, sistemas agênticos, multi-agente, copilotos conversacionais | — | "Ao menos um caso de agentes de IA em produção"; "Familiaridade com arquiteturas modernas baseadas em agentes (arquitetura agêntica)" |
| Ciência de dados e machine learning | `ia.ciencia_dados_ml` | modelos preditivos, ML, estatística aplicada, forecast, séries temporais | "IA" genérica sem ML vai em "IA aplicada ao negócio" | "Base sólida em estatística, machine learning e desenho de experimentos…"; "Séries temporais, forecast, segmentação, modelos de propensão…" |
| MLOps e LLMOps | `ia.mlops` | colocar e manter modelo em produção, monitorar drift, ciclo de vida de modelo, feature store | — | "Familiaridade com práticas de MLOps e deploy de modelos de Machine Learning em produção"; "LLMOps e frameworks de avaliação de modelos em produção…" |
| IA aplicada ao negócio | `ia.ia_aplicada` | aplicar IA a problemas ou áreas, estratégia/portfólio de IA, casos de uso, ROI de IA | — | "Fomentar a utilização de analytics, inteligência artificial e novas tecnologias aplicadas ao negócio"; "Definir e liderar a estratégia de IA … governar o portfólio" |
| IA na produtividade do time | `ia.ia_produtividade` | usar IA no próprio trabalho do time: AI-first engineering, copilots, acelerar entrega | — | "Impulsionar práticas de AI-first engineering…"; "Uso de ferramentas de IA generativa e agentes para acelerar o trabalho do time" |

### Formação, idioma e experiência

| item | chave | definição | borda | exemplos reais |
|---|---|---|---|---|
| Graduação | `formacao.graduacao` | ensino superior (qualquer área ou áreas listadas) | — | "Ensino superior completo em Tecnologia, Engenharia, Ciência da Computação ou áreas correlatas"; "Formação superior completa em áreas correlatas" |
| Pós-graduação, MBA, mestrado | `formacao.pos` | pós, MBA, mestrado, doutorado | — | "Pós-graduação ou MBA em Gestão, Dados ou Tecnologia é diferencial"; "Mestrado ou doutorado em áreas relacionadas a Data Science…" |
| Certificação | `formacao.certificacao` | certificação (cloud, BI, Scrum, governança) | — | "Certificações em cloud"; "Certificações na área de dados (Azure Data Engineer, AWS…)" |
| Inglês | `idioma.ingles` | inglês, em qualquer nível | — | "Inglês avançado para comunicação verbal e escrita"; "Excellent level of English C1 or above" |
| Espanhol | `idioma.espanhol` | espanhol, em qualquer nível | — | "Espanhol Avançado/Fluente (Mandatório)"; "Desejável: Espanhol" |
| Tempo de experiência | `experiencia.anos` | pede N anos (na área, em liderança); o número vai no rótulo `anos` | — | "10 a 15 anos de experiência em tecnologia, com ao menos 5 anos em posições de liderança…"; "Experiência acima de 5 anos em call center" |
| Experiência prévia na área de dados | `experiencia.dados` | pede trajetória ou experiência sólida em dados, BI, engenharia ou ciência (sem nomear prática específica) | se nomeia a prática ("experiência com pipelines"), marca a prática | "Sólida experiência prévia em Data Analytics"; "Experiência prévia atuando em áreas de Ciência de Dados, Analytics ou Engenharia de Dados" |
| Experiência setorial | `experiencia.setor` | pede experiência num setor ou negócio; o **setor** vai num 2º campo, com a mesma lista de `setores.csv` | conhecimento de negócio específico ("crédito e cobrança", "chargeback", "folha de pagamento") conta, com o setor dele | "Experiência no setor financeiro ou em áreas corporativas de alta complexidade"; "Diferencial: experiência em healthtechs, edtechs…" |

### Comportamental e condições

| item | chave | definição | borda | exemplos reais |
|---|---|---|---|---|
| Comunicação e colaboração | `comportamento.comunicacao` | comunicação clara, colaboração, interação com níveis diferentes | apresentação executiva vai em "comunicação executiva" | "Boa comunicação e habilidade para interagir com diferentes níveis de stakeholders"; "Strong communication skills…" |
| Pensamento analítico e resolução de problemas | `comportamento.analitico` | capacidade analítica, pensamento crítico, estruturar problema, causa raiz | — | "Forte afinidade com dados, excelente capacidade analítica e pensamento crítico"; "'Dive deep'… identificar a causa raiz…" |
| Autonomia e iniciativa | `comportamento.autonomia` | autonomia, perfil empreendedor, inquieto, curiosidade, proatividade | — | "Perfil empreendedor e inovador, com autonomia para propor e executar sem precisar de tutela"; "Senioridade suficiente para atuar com autonomia…" |
| Organização e ambiente de pressão | `comportamento.organizacao` | organização, prioridades concorrentes, pressão, adaptabilidade, ritmo acelerado | — | "Capacidade de priorizar demandas e trabalhar sob pressão"; "Lidar com necessidades/prioridades concorrentes… em contexto acelerado" |
| Condição de trabalho | `condicao.trabalho` | viagens, presencial/híbrido, mudança de cidade | — | "Disponibilidade para viagens"; "Disponibilidade para trabalhar em modelo híbrido (3 vezes por semana no escritório)…" |
| Outro | `outro` | nada acima cabe; escrever 3–6 palavras | — | "Gerenciar as rotinas executivas … papéis de liderança em Saúde e Segurança" |

é gestão de pessoas × estratégia × técnica…); o item é o detalhe.

## Ferramentas

Ferramenta citada pelo nome **não** é rotulada pelo modelo: o dicionário `dbt/seeds/ferramentas.csv` (nome canônico e
sinônimos) marca por regra. Nome que não está no dicionário fica sem marca e aparece num relatório de nomes não
reconhecidos, pra entrar no dicionário na rodada seguinte.
