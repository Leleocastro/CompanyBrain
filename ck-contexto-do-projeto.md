# CompanyKnowledge (CK) — Contexto do projeto

Documento de contexto para quem vai montar a equipe e trabalhar neste projeto (humanos e agentes de IA). Descreve o produto e a arquitetura-alvo. Reúne apenas o que foi informado pelo fundador e o que consta em um artigo de referência. Nada foi inventado: onde o material não define algo, está dito (seção 12).

---

## 0. Como ler este documento

**Fontes usadas**
- **Especificação do fundador**: o texto "Visão do produto / Arquitetura técnica / Funcionalidades por jornada / Segurança / Cobrança / Ordem de construção / Fora do escopo". É a fonte principal. As seções 2, 5, 6, 7, 8 e 9 vêm dela.
- **Artigo de referência**: "Construí uma memória para a empresa inteira: tudo vira documentação sozinho", de Leonardo Castro (Medium, 16/10/2026). Descreve um sistema que faz algo muito parecido. As seções 3 e 10 vêm dele.
- **Mensagens do fundador** sobre o objetivo atual (seção 1).
- O fundador também indicou um post no X sobre o assunto. Ele não pôde ser lido, então nada dele está refletido aqui.

**Regras de leitura**
- O conteúdo do repositório **CompanyBrain não foi inspecionado** ao escrever este documento. Nada aqui descreve o código atual.
- Para saber **como é hoje**: vale o repositório. Para saber **como deve ser**: vale este documento.
- Se os dois divergirem, ou se este documento não responder algo, **não decida sozinho**: registre e pergunte ao fundador.
- O fundador diz que a plataforma "já existe" e que o sistema "você já opera hoje" (texto da especificação). O artigo descreve um sistema com a mesma ideia, mas este documento **não confirma** que ele seja o mesmo código do CompanyBrain. Isso deve ser verificado no repositório.
- Os termos "tenant" e "workspace" aparecem na especificação de forma intercambiável (ex.: "custo de tokens por workspace", "lista de tenants", "exclusão do workspace").

---

## 1. Objetivo atual do projeto

- **Nome:** CompanyKnowledge, abreviado **CK**. O nome é provisório ("até então").
- **Situação:** a plataforma já existe como sistema interno do fundador (repositório GitHub **CompanyBrain**). Ela precisa "rodar em algum lugar", e esse lugar será um **GitHub App**.
- **Meta:** criar um app dentro do GitHub onde o usuário (dev) possa utilizar a plataforma facilmente.
- **O que a especificação diz que muda em relação ao sistema que já roda:** a camada multi-tenant, o juiz "Jev" nas regras de negócio, o backfill como porta de entrada, e a disciplina de custo por cliente com alertas, que transformam o projeto interno em serviço pago.
- **Como será construído:** por uma equipe de agentes de IA coordenada no Multica.

---

## 2. Visão do produto

"Memória como serviço": empresas conectam suas fontes de conhecimento (código, documentos, conversas) e recebem de volta:

1. uma **wiki viva** que se atualiza sozinha;
2. um **chat** que responde com base em tudo que foi registrado;
3. uma **API/MCP** para agentes de IA consultarem essa memória.

**Cobrança:** assinatura com base fixa mais uso excedente.

**Distribuição:** como GitHub App. O dev instala em 1 clique (OAuth), escolhe os repositórios e passa a ter a memória gerada a partir dos PRs. Documentos enviados e o endpoint `/v1/ingest` completam as fontes.

---

## 3. Problema e tese (do artigo)

Toda empresa de software tem o mesmo vazamento invisível de conhecimento:
- o conhecimento real mora nos PRs mergeados, nas conversas e na cabeça de quem já saiu;
- a wiki oficial está sempre desatualizada, porque atualizá-la exige esforço manual depois que o trabalho acabou;
- o onboarding de um dev novo vira uma caça ao tesouro.

**Tese:** documentação tratada como "documento" morre; tratada como **pipeline**, se mantém sozinha. Princípios do artigo:
1. Conhecimento antes de documentação: a doc é um artefato gerado a partir do conhecimento existente.
2. Automação primeiro: documentos gerados automaticamente sempre que possível.
3. Rastreabilidade: todo conhecimento gerado indica sua origem (repositório, arquivo, PR).
4. Fonte única de verdade: um lugar central onde o conhecimento consolidado vive.

---

## 4. Quem interage com o produto

(Descrito a partir da especificação; os papéis não têm nomes formais no material.)

- **O dev / a empresa cliente:** instala o GitHub App, escolhe os repositórios, conecta fontes, cria e revoga API keys, convida membros do time, acompanha uso e cobrança.
- **Membros do time convidados:** buscam na wiki e perguntam no chat; podem avaliar respostas (joinha/negativo).
- **Revisor humano:** revisa, na fila de revisão, as regras que o Jev não aprovou nem rejeitou automaticamente.
- **Agentes de IA do cliente:** consultam a memória da empresa programaticamente, via REST ou MCP, com API key.
- **Fundador (admin do fundador):** opera a plataforma, vê a saúde e o custo por tenant, atua em falhas, dá suporte (impersonação, kill switch).

---

## 5. Arquitetura técnica (especificação do fundador)

### Backend
- **FastAPI, multi-tenant.** Todo request carrega `tenant_id`.
- **Autenticação dupla:** API key (para ingestão e integrações) e sessão (para painel, wiki e chat).
- **Rate limiting por tenant** no Redis.

### Ingestão
- **GitHub App:** instalação em 1 clique (OAuth), webhooks de PRs, leitura de código para contexto.
- **Upload de documentos** no painel (PDF, Markdown, TXT).
- **`POST /v1/ingest`:** endpoint genérico para atas, conversas, notas e qualquer texto.
- **Fila assíncrona (Redis)** entre a chegada do dado e o processamento, para absorver picos e o backfill.

### Pipeline de processamento (via LiteLLM)
- **PRs:** resumo estruturado com modelo barato, gera Markdown versionado.
- **Documentos:** chunking e normalização para Markdown.
- **Crons diário e semanal:** analisam o acumulado e extraem candidatas a regras de negócio e ADRs.
- **Verificação com Jev (TypeSafe):**
  - o "state" da chamada é a fonte mais a regra candidata;
  - perguntas tipadas por afirmação: `noul` para fidelidade e `choice` para escopo, com as opções `adequada`, `super_generalizada` e `trivial` (grafia conforme a especificação);
  - três bandas por confiança calibrada: **alta** auto-aprova, **baixa** auto-rejeita ou regenera, **meio** vai para revisão humana.
- **Fila de revisão humana:** só a banda do meio, com a fonte e a regra lado a lado. A especificação explica o motivo: o Jev não explica o veredito, então o humano precisa do contexto visual.

### Armazenamento
- **Postgres:** tenants, usuários, documentos, regras (status: sugerida, aprovada, rejeitada), assinaturas, eventos de uso, trilha de auditoria (fonte, regra, veredito do Jev, score).
- **Qdrant:** embeddings com isolamento por tenant (coleção por tenant ou filtro por campo `tenant_id`).
- **Redis:** filas, cache de respostas frequentes, controle de uso em tempo real.
- **Object storage (S3):** documentos originais e builds estáticos da wiki.

### Wiki (estilo Quartz)
Build estático por tenant, servido em subdomínio próprio por cliente. Inclui busca full-text mais semântica, graph view dos documentos relacionados, versionamento com histórico ("quando mudou e por quê") e citações de origem em cada página.

### Chat (um motor, duas superfícies)
- **Motor RAG único:** recuperação no Qdrant, rerank, resposta do LLM sempre com citações das fontes.
- **Superfície 1:** embutida na wiki, para pesquisa contextual.
- **Superfície 2:** standalone, estilo ChatGPT/OpenWebUI, com histórico de conversas por usuário e botões de joinha/negativo em cada resposta para melhorar o retrieval.

### MCP e API pública
- API REST documentada (ingestão e consulta).
- Servidor MCP via HTTP com API key no v1, expondo ferramentas como `search_memory`, `get_document` e `ask`.
- OAuth no MCP fica para o enterprise, depois.

### Billing (Stripe)
Assinatura da base fixa mais cobrança medida do excedente; portal de cobrança do Stripe embutido no painel (faturas, troca de cartão, upgrade); medição por eventos (documento ingerido, pergunta no chat).

### Painel do cliente
Conectar e gerenciar fontes (status de cada uma, religar GitHub), criar e revogar API keys, dashboard de uso da franquia com alertas em 70% e 90%, trava de gasto configurável (ao atingir o teto, pausa o excedente em vez de cobrar), pacotes adicionais de uso, convite de membros do time.

### Admin do fundador
Lista de tenants com saúde, custo de tokens por workspace (essencial para proteger a margem no modelo híbrido), status da pipeline por tenant, alertas de falha (GitHub desconectado, ingestão falhando, fila acumulando), kill switch por tenant, impersonação para suporte.

### Observabilidade
Logs estruturados sempre com `tenant_id`, métricas de latência e erro por etapa do pipeline, alertas proativos antes do cliente perceber.

---

## 6. Funcionalidades em detalhe, por jornada (especificação do fundador)

**Cadastro e onboarding**
Signup, criação do workspace, convite de membros por e-mail, instalação do GitHub App escolhendo repositórios, upload inicial de documentos ou chamada ao `/ingest`. Ao conectar um repositório, dispara o **backfill histórico**: importa PRs passados automaticamente (3 meses no Essencial, 12 no Profissional, gratuito sem backfill), processado em background com modelo barato em lote, pulando PRs de bot, merges e PRs minúsculos, com teto de volume por segurança.

**Captura contínua**
Todo PR novo gera um resumo versionado. Documentos enviados viram páginas da wiki. Os crons diário e semanal propõem regras de negócio e ADRs, verificadas pelo Jev e aprovadas automaticamente ou enviadas à fila humana.

**Consulta**
Buscar na wiki; perguntar no chat (com citações clicáveis); navegar pelo grafo de documentos relacionados; ver o histórico de versões de qualquer página.

**Integração para agentes**
A API key dá acesso ao REST e ao MCP, para os agentes de IA do cliente consultarem a memória da empresa programaticamente.

**Gestão e cobrança**
Tudo do painel do cliente descrito na seção 5, mais a trava de gasto e os pacotes de expansão como forma padrão de vender excedente.

---

## 7. Segurança, isolamento e LGPD (especificação do fundador)

- Isolamento lógico total por `tenant_id` em banco, vetores e storage.
- API keys com hash e escopos.
- Exclusão do workspace apaga todos os dados (vetores, documentos, regras, conversas).
- Botão de exportar todos os dados do workspace.
- Retenção configurável.
- Nada de dados de um cliente alimenta modelo ou vaza para outro.

---

## 8. Modelo de cobrança (especificação do fundador)

| Plano | Preço | Fontes | Documentos | Perguntas | Backfill |
|---|---|---|---|---|---|
| Gratuito (isca) | — | 1 | — | — | sem backfill |
| Essencial | R$ 249/mês | 3 | 2.000 | 500 | 3 meses |
| Profissional | R$ 599/mês | 10 | 10.000 | 3.000 | 12 meses |
| Enterprise | sob consulta | — | — | — | — |

- "Gratuito limitado" tem 1 fonte e não tem backfill; a especificação não define os demais limites dele.
- **Excedente em pacotes:** R$ 49 a cada 1.000 documentos; R$ 39 a cada 1.000 perguntas. Com trava de gasto e opt-in.
- **Enterprise:** inclui SSO, domínio próprio e "traga sua chave"; fica para depois do v1.
- O painel traz pacotes adicionais, alertas em 70% e 90% da franquia e trava de gasto configurável.

---

## 9. Ordem de construção e fora do escopo (especificação do fundador)

**Fase 1: fundação**
Fundação multi-tenant (auth, `tenant_id`, API keys), GitHub App, backfill, pipeline de PRs, wiki por tenant, chat nas duas superfícies, Stripe com a base fixa.

**Fase 2**
Upload de documentos e `/ingest`; crons de regras com verificação Jev e fila de revisão humana; medição de uso; painel do cliente completo (trava de gasto, pacotes); admin com custo por tenant e alertas de falha.

**Fase 3**
MCP e API pública documentada; demo pública com repositório open-source famoso; landing page com lista de espera e piloto de 14 dias.

**Depois**
MCP com OAuth, SSO, papéis granulares, conectores (Slack, Drive, Notion), domínio próprio por cliente, backfill enterprise profundo como projeto de implantação cobrado à parte.

**Fora do escopo do v1, "sem culpa"**
SSO, permissões granulares por usuário, app mobile, múltiplos idiomas na interface, SLA contratual de uptime, região dedicada por cliente.

---

## 10. Referência: o sistema descrito no artigo

(Informação do artigo. Serve de referência de como um sistema parecido foi construído. Não é especificação do CK: ver seção 0.)

**Fluxo ("o loop que se auto-alimenta")**
1. Um dev abre/mergeia um PR; o webhook chega na API.
2. A API indexa o código (chunks + embeddings no Qdrant, metadados no Postgres).
3. Um agente (LLM) analisa o diff e gera Markdown estruturado: regras de negócio, decisões arquiteturais, novas integrações, riscos.
4. O Markdown é commitado no repositório de conhecimento.
5. O novo commit re-indexa o conteúdo gerado: o conhecimento produzido vira dado pesquisável.
6. A API dispara o rebuild da wiki: pull do repositório, injeção de "documentos relacionados" e build estático.

**Camadas e stack do original**
- Quatro camadas: ingestão, geração, memória e consumo; tudo em containers (Docker Compose).
- Stack: FastAPI, LiteLLM, AWS Bedrock (Claude), Qdrant, Postgres, Redis, Quartz, Open WebUI, GitHub Actions e Docker. O LiteLLM é usado como gateway para trocar de provedor sem reescrever.
- Memória em três camadas: Markdown versionado no Git (fonte da verdade), banco vetorial (Qdrant) e Postgres + Redis (metadados, histórico, fila).
- Webhooks do GitHub (`pull_request`, `push`) assinados com secret e verificados por HMAC.
- Exemplo do artigo de indexação: `chunk_text(markdown, size=800, overlap=100)` (unidade não informada).

**Agentes especializados do original** (cada um com prompt versionado no Git)

| Agente | Gatilho | Gera |
|---|---|---|
| Analisador de PRs | Webhook (PR mergeado) | Análise por PR: regras de negócio, decisões arquiteturais, integrações, riscos |
| Agente de ADRs | Agendado (diário) | Architecture Decision Records |
| Analista de arquitetura | Agendado (semanal) | Visão consolidada da arquitetura |
| Analista de regras de negócio | Agendado (semanal) | Regras de negócio consolidadas |

Há endpoints administrativos para rodar cada agente manualmente e fazer backfill histórico.

**Convenções do original**
- `gerado/` vs `manual/`: tudo que é 100% gerado por IA vive em um diretório que ninguém edita à mão; capturas humanas (ou feitas por IAs via MCP) vão para outro. Sem isso, uma regeneração destrói edição humana.
- Prompts como código: os prompts dos agentes são arquivos Markdown versionados.

**Busca e MCP do original**
A consulta vira embedding e o Qdrant devolve os chunks mais similares. O servidor MCP expõe ferramentas de leitura (`knowledge_search`, `knowledge_find_rule`, `knowledge_find_decision`, `knowledge_find_similar_issue`, `knowledge_list`) e de escrita (`knowledge_capture`, que grava na área manual). Observação: os nomes das ferramentas do CK (seção 5) são outros.

**Publicação no original**
- Wiki estática (Quartz): busca instantânea (Ctrl+K), explorador de arquivos, graph view e backlinks. Antes do build, um script faz uma busca semântica para cada documento e anexa uma seção "Documentos relacionados".
- Chat com RAG (Open WebUI): interface apontada para um proxy compatível com OpenAI que busca o contexto no cérebro e o injeta no prompt antes de chamar o modelo; a resposta cita a fonte.

**Lições aprendidas do original**
1. **Modelos de IA têm fim de vida:** o provedor aposentou o modelo usado pelos agentes e o pipeline parou sem aviso. Tratar modelos como dependências, pinar versões, monitorar "documentos gerados nas últimas N horas" e alertar quando o pipeline ficar mudo.
2. **Proxy truncando JSON grande:** o índice de busca da wiki (`contentIndex.json`), com mais de 1 MB, foi truncado por um proxy reverso com buffering/cache, sem erro visível; o explorador de arquivos e o graph view ficaram vazios. Servir arquivos grandes sem buffering agressivo e carregar o índice de forma incremental.
3. **Versionar a ferramenta, não só o conteúdo:** o código do pipeline de ingestão não estava em nenhum repositório (só a imagem do container). Se não dá para reconstruir o pipeline do zero a partir de um repositório, é um ponto único de falha invisível.
4. **Separar o gerado do manual**, ou a automação destrói trabalho humano.
5. **Rastreabilidade gera confiança:** cada documento gerado cita sua origem (repositório, PR, arquivo).

**Próximos passos que o artigo cita** (ideias do autor, não compromissos do CK): busca híbrida (vetorial + BM25 com fusão de rankings), avaliação contínua por um agente "crítico", sumários executivos periódicos e mais fontes (decisões de incidentes, RFCs de arquitetura).

---

## 11. Termos usados

- **Tenant / workspace:** o espaço isolado de um cliente na plataforma (ver nota na seção 0).
- **Fonte:** origem de conhecimento conectada pelo cliente: repositório GitHub (via GitHub App), documentos enviados, ou texto enviado a `/v1/ingest`.
- **Franquia:** limites de fontes, documentos e perguntas de um plano.
- **Backfill:** importação em background dos PRs passados ao conectar um repositório.
- **Trava de gasto:** teto configurável que, ao ser atingido, pausa o excedente em vez de cobrar.
- **Pacote adicional:** unidade de venda do excedente (por 1.000 documentos ou 1.000 perguntas).
- **Regra de negócio / ADR:** conhecimento extraído e proposto pelos crons; a regra tem status sugerida, aprovada ou rejeitada. ADR = Architecture Decision Record (registro de decisão de arquitetura).
- **Jev (TypeSafe):** o verificador que atribui um veredito e uma confiança às regras candidatas; não explica o veredito.
- **Bandas de confiança:** alta (auto-aprova), baixa (auto-rejeita ou regenera), meio (revisão humana).
- **Citação:** referência à origem (repositório, arquivo, PR) em cada página da wiki e em cada resposta do chat.
- **RAG:** resposta do LLM fundamentada no que foi recuperado da base vetorial.
- **MCP:** Model Context Protocol; no CK, a forma de agentes de IA consultarem a memória.
- **`gerado/` vs `manual/`:** convenção do artigo para separar conteúdo 100% gerado por IA de capturas humanas ou via MCP.
- **Pipeline mudo:** quando o pipeline para de gerar documentos sem erro visível (lição 1 do artigo).
- **Kill switch / impersonação:** ferramentas do admin do fundador para pausar um tenant e para dar suporte vendo como o cliente.

---

## 12. O que o material não define (perguntas em aberto)

Estes pontos **não estão definidos** na especificação nem no artigo. Antes de perguntar ao fundador, confira se o repositório CompanyBrain já responde.

1. **Estado atual e estrutura do repositório CompanyBrain**, e se ele é o mesmo sistema descrito no artigo.
2. **Critério de "pronto" de cada fase** (a especificação lista o que entra em cada fase, mas não como saber que ela terminou).
3. **Permissões do GitHub App** (quais permissões e eventos) e **como ele será registrado/publicado** (conta ou organização dona; Marketplace ou não).
4. **Onde vive o Markdown versionado no SaaS.** A especificação diz "Markdown versionado", Postgres com documentos e S3 com documentos originais e builds; o artigo usa um repositório Git. Não está definido qual será o modelo no CK.
5. **Contrato da API do Jev** e a forma exata de montar o "state".
6. **O que o revisor humano pode fazer na fila** (só aprovar/rejeitar, ou também editar a regra).
7. **O que acontece ao esgotar a franquia sem pacote adicional** (a especificação define a trava de gasto e o opt-in do excedente, mas não esse caso).
8. **Domínio base e DNS** dos subdomínios das wikis.
9. **Modelos por etapa e custo-alvo** por documento e por pergunta (a especificação só diz "modelo barato" para PRs e backfill, e que o LiteLLM é o gateway; embeddings, rerank e LLM do chat não estão definidos).
10. **Hospedagem e ambientes** (onde o SaaS roda; como serão dev, staging e produção). A especificação não trata disso.
11. **Idioma da interface no v1** (a especificação exclui múltiplos idiomas, mas não diz qual idioma único).
12. **Limites do plano gratuito** além de "1 fonte, sem backfill".
