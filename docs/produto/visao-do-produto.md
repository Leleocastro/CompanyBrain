# CompanyKnowledge — visão de produto (Fase 0)

Documento de produto da Fase 0 (Entendimento). Descreve **o alvo** a partir de `ck-contexto-do-projeto.md` e **o que já existe** no repositório CompanyBrain (branch `main`, commit `4e37951`).

Regras deste documento:
- Toda afirmação traz a origem: seção do arquivo de contexto (`§N`) ou caminho no repositório (`caminho:linha`).
- O repositório manda para "como é hoje"; o contexto manda para "como deve ser" (`ck-contexto-do-projeto.md` §0).
- O que o material não define está em **Perguntas em aberto** (§9 deste documento). Nada foi suposto como fato.

---

## 1. O que é o CompanyKnowledge

"Memória como serviço": a empresa conecta suas fontes de conhecimento (código, documentos, conversas) e recebe de volta (`§2`):

1. uma **wiki viva** que se atualiza sozinha;
2. um **chat** que responde com base em tudo que foi registrado;
3. uma **API/MCP** para agentes de IA consultarem essa memória.

- **Distribuição:** GitHub App; o dev instala em 1 clique (OAuth), escolhe repositórios, e a memória é gerada a partir dos PRs. Documentos enviados e o endpoint `/v1/ingest` completam as fontes (`§2`).
- **Cobrança:** assinatura com base fixa mais uso excedente (`§2`, `§8`).
- **Nome:** CK é provisório (`§1`).
- **Tese de produto:** documentação tratada como documento morre; tratada como **pipeline**, se mantém sozinha. Conhecimento antes de documentação, automação primeiro, rastreabilidade e fonte única de verdade (`§3`).

---

## 2. O que já existe no repositório (estado atual)

O CompanyBrain é um monorepo com cinco serviços — `ingestao`, `indexer`, `graph`, `api`, `web` (`README.md:1`). O que existe hoje é **a camada de conectores de ingestão e um esboço de API/web**; o restante da Fase 1 não está no código.

| Área | O que existe | Origem |
|---|---|---|
| API | FastAPI "Mock Graph API" com dados em memória (~20 nós, ~30 arestas) e endpoints `/api/health`, `/api/graph/nodes`, `/api/graph/edges`, `/api/graph/search`, `/api/graph/node/{id}`; CORS restrito a `http://localhost:5173` | `api/mock_graph/main.py:7`, `:12`, `:88`-`118` |
| Web | SPA React 18 + Vite + d3-force com visualização de grafo estilo Obsidian, consumindo dados mock | `web/README.md:1`, `web/package.json:1` |
| Ingestão — contrato | `BaseConnector` (ABC: authenticate, list_files, download, extract_metadata, ingest) e `Document` normalizado | `ingestao/connectors/base.py:1` |
| Ingestão — Slack | Connector com auth, client, canais, threads, normalização e CLI | `ingestao/connectors/slack/` |
| Ingestão — Google Drive | Connector completo (client, models, normalizer) + README | `ingestao/connectors/google_drive/` |
| Ingestão — Gmail | Scaffolding (auth, config, client, parser, testes) | `ingestao/connectors/gmail/` |
| Ingestão — GitHub | Client REST (commits, PRs, issues), auth OAuth/GitHub App/PAT via env, normalizer, ingestor com `since`, webhooks com verificação HMAC (`X-Hub-Signature-256`) para `push` e `pull_request` | `ingestao/github_connector/auth.py:15`, `client.py:1`, `ingestor.py:1`, `webhooks.py:24` |
| Ingestão — apoio | Modelos `SourceDocument`, normalização de sha256/timestamp, redação de PII | `ingestao/models.py:1`, `ingestao/normalizer.py:1`, `ingestao/pii.py:1` |
| Indexer / Graph | Placeholders (apenas README e `.placeholder`) | `indexer/README.md:1`, `graph/README.md:1` |
| Empacotamento | Dockerfile por serviço (api, indexer, graph, ingestao, web) e `web.nginx.conf` | `docker/` |
| CI/CD | Workflow por serviço (lint → test; build no web) e deploy staging/prod via `ghcr.io` | `.github/workflows/service-*.yml`, `scripts/deploy-staging.sh:1` |

**Não existe no `main`:** persistência (Postgres/Redis), banco vetorial (Qdrant), chamadas a LLM/LiteLLM, `tenant_id`, autenticação de API keys ou sessão, `/v1/ingest`, pipeline de resumo de PR, build de wiki (Quartz), chat, MCP, Stripe/billing, painel do cliente, admin do fundador e pasta de documentação.

Consequência para o planejamento: **quase todo o escopo da Fase 1 (§9) é construção nova**, exceto o connector GitHub (`ingestao/github_connector/`) e o esqueleto de API/web, que são a base a aprimorar.

---

## 3. Quem interage com o produto

Papéis descritos na especificação, sem nomes formais (`§4`):

- **Dev / empresa cliente:** instala o GitHub App, escolhe repositórios, conecta fontes, cria e revoga API keys, convida membros, acompanha uso e cobrança.
- **Membros do time convidados:** buscam na wiki, perguntam no chat e avaliam respostas (joinha/negativo).
- **Revisor humano:** decide, na fila de revisão, as regras que o Jev não aprovou nem rejeitou automaticamente.
- **Agentes de IA do cliente:** consultam a memória via REST/MCP com API key.
- **Fundador (admin):** opera a plataforma, vê saúde e custo por tenant, atua em falhas, dá suporte (impersonação, kill switch).

---

## 4. Jornadas (`§6`)

**4.1 Cadastro e onboarding**
Signup, criação do workspace, convite de membros por e-mail, instalação do GitHub App escolhendo repositórios, upload inicial de documentos ou chamada ao `/ingest`. Ao conectar um repositório, dispara o **backfill histórico** de PRs (3 meses no Essencial, 12 no Profissional; gratuito sem backfill), processado em background, pulando PRs de bot, merges e PRs minúsculos, com teto de volume.

**4.2 Captura contínua**
Todo PR novo gera um resumo versionado. Documentos enviados viram páginas da wiki. Crons diário e semanal propõem regras de negócio e ADRs, verificadas pelo Jev e aprovadas automaticamente ou enviadas à fila humana.

**4.3 Consulta**
Buscar na wiki, perguntar no chat (com citações clicáveis), navegar pelo grafo de documentos relacionados e ver o histórico de versões de qualquer página.

**4.4 Integração para agentes**
A API key dá acesso ao REST e ao MCP para os agentes do cliente consultarem a memória programaticamente (`§6`; detalhe de endpoints em `§5`).

**4.5 Gestão e cobrança**
Painel do cliente: status das fontes, religar GitHub, criar/revogar API keys, dashboard de uso com alertas em 70% e 90%, trava de gasto, pacotes adicionais e convites (`§5`, `§6`).

---

## 5. Planos e cobrança (`§8`)

| Plano | Preço | Fontes | Documentos | Perguntas | Backfill |
|---|---|---|---|---|---|
| Gratuito (isca) | — | 1 | — | — | sem backfill |
| Essencial | R$ 249/mês | 3 | 2.000 | 500 | 3 meses |
| Profissional | R$ 599/mês | 10 | 10.000 | 3.000 | 12 meses |
| Enterprise | sob consulta | — | — | — | — |

- **Excedente em pacotes:** R$ 49 por 1.000 documentos; R$ 39 por 1.000 perguntas, com trava de gasto e opt-in (`§8`).
- **Enterprise** inclui SSO, domínio próprio e "traga sua chave"; fica para depois do v1 (`§8`).
- O plano gratuito não tem os demais limites definidos (`§8`, `§12.12`).
- Ferramenta de cobrança: Stripe, com portal embutido no painel (faturas, troca de cartão, upgrade) e medição por evento — documento ingerido, pergunta no chat (`§5`).

---

## 6. Fases e o que falta em cada uma (`§9`)

| Fase | Escopo definido no contexto | Existe no repo hoje | Lacuna |
|---|---|---|---|
| **1 — Fundação** | Fundação multi-tenant (auth, `tenant_id`, API keys), GitHub App, backfill, pipeline de PRs, wiki por tenant, chat nas duas superfícies, Stripe com base fixa | connector GitHub (`ingestao/github_connector/`), esqueleto de API mock (`api/mock_graph/`) e web de grafo (`web/src/`) | tenant/auth, persistência, fila, GitHub App instalável, backfill, resumo de PR, wiki, chat, Stripe |
| **2** | Upload de documentos e `/v1/ingest`; crons de regras com Jev e fila de revisão; medição de uso; painel completo (trava de gasto, pacotes); admin com custo por tenant e alertas | conectores Slack/Drive/Gmail prontos para alimentar fontes | pipeline de documentos, Jev, uso, painel, admin |
| **3** | MCP e API pública documentada; demo pública com repositório open-source; landing page com lista de espera e piloto de 14 dias | — | tudo |
| **Depois** | MCP com OAuth, SSO, papéis granulares, conectores (Slack, Drive, Notion), domínio próprio, backfill enterprise | conectores Slack/Drive/Gmail já existem como código de ingestão | MCP/OAuth, SSO, papéis, domínio, implantação |

**Fora do escopo do v1, "sem culpa":** SSO, permissões granulares por usuário, app mobile, múltiplos idiomas na interface, SLA contratual de uptime, região dedicada por cliente (`§9`).

Observação: os conectores Slack, Google Drive e Gmail existentes (`ingestao/connectors/`) **não estão na Fase 1 nem na Fase 2** da ordem de construção; a especificação coloca conectores em "Depois". Eles são base pronta, não demanda da Fase 1.

---

## 7. Glossário (`§11`)

- **Tenant / workspace:** espaço isolado de um cliente; os dois termos são usados de forma intercambiável na especificação (`§0`).
- **Fonte:** repositório GitHub (via GitHub App), documentos enviados ou texto via `/v1/ingest`.
- **Franquia:** limites de fontes, documentos e perguntas de um plano.
- **Backfill:** importação em background dos PRs passados ao conectar um repositório.
- **Trava de gasto:** teto que, ao ser atingido, pausa o excedente em vez de cobrar.
- **Pacote adicional:** unidade de venda do excedente (por 1.000 documentos ou 1.000 perguntas).
- **Regra de negócio / ADR:** conhecimento proposto pelos crons; a regra tem status sugerida, aprovada ou rejeitada.
- **Jev (TypeSafe):** verificador que atribui veredito e confiança às regras candidatas; não explica o veredito.
- **Bandas de confiança:** alta (auto-aprova), baixa (auto-rejeita ou regenera), meio (revisão humana).
- **Citação:** referência à origem (repositório, arquivo, PR) em cada página e em cada resposta do chat.
- **RAG:** resposta do LLM fundamentada no que foi recuperado da base vetorial.
- **MCP:** Model Context Protocol; no CK, a forma de agentes consultarem a memória.
- **Pipeline mudo:** pipeline que para de gerar documentos sem erro visível (`§10`, lição 1).

---

## 8. Quem decide o quê

Origem desta seção: instruções do projeto no Multica (papéis, colunas do board e regras R1–R16) — não é produto nem código.

- **João Pedro Rocha (fundador):** decide produto, escopo, preço, contratos e tudo que bloqueia o trabalho; aprova o fim de cada fase. É a única instância de dúvida (`blocked`).
- **po:** mantém o backlog, escreve critérios de aceite verificáveis, faz o aceite final e reabastece o pipeline.
- **tech-lead:** refina tecnicamente, decide arquitetura, onde vivem documentação e skills, e quebra cards grandes.
- **dev-backend / dev-frontend / devops:** implementam.
- **reviewer:** revisa PRs (feedback no PR, nunca no card).
- **qa:** valida em staging (cards de código; cards `docs` não passam por QA).
- **Regra de ouro:** só trabalha em card atribuído a si; handoff é ação (corpo do card + status + atribuição), nunca conversa.

---

## 9. Premissas

- A pasta `docs/produto/` foi criada por este documento porque o tech-lead ainda não decidiu onde vivem docs e skills (card "Fase 0 — documentação técnica e cards de entendimento"). Pode ser movida pelo tech-lead.
- "Tenant" e "workspace" são tratados como sinônimos (`§0`).
- O documento descreve o estado do `main` no commit `4e37951`; branches de trabalho em andamento não foram consideradas como existentes.
- Os conectores Slack/Drive/Gmail existentes não entram no roadmap da Fase 1 (a especificação os coloca em "Depois", `§9`).

---

## 10. Perguntas em aberto

1. **Estado do repositório vs. plataforma "que já existe" (`§1`, `§12.1`).** O `main` só tem conectores, API mock e web de grafo. O fundador descreve uma plataforma que "já opera hoje". Esse código está fora do CompanyBrain ou a Fase 1 parte do zero nessas peças?
2. **Entrypoint do serviço API.** `docker/api.Dockerfile:12` executa `uvicorn api.main:app`, mas o módulo existente é `api/mock_graph/main.py`. Qual é o entrypoint oficial? (Encaminhado ao tech-lead.)
3. **Critério de "pronto" por fase (`§12.2`).** A especificação lista o que entra em cada fase, mas não como verificar que ela terminou.
4. **GitHub App (`§12.3`).** Quais permissões e eventos? Registrado em conta pessoal ou organização? Publicado no Marketplace?
5. **Onde vive o Markdown versionado (`§12.4`).** Git, Postgres ou S3? `§5` cita "Markdown versionado", "documentos no Postgres" e "documentos originais no S3" sem definir o modelo no SaaS.
6. **Contrato do Jev (`§12.5`).** Formato exato do "state" e da chamada (Fase 2, mas define o desenho do pipeline).
7. **Poderes do revisor humano (`§12.6`).** Só aprovar/rejeitar ou também editar a regra?
8. **Franquia esgotada sem pacote (`§12.7`).** Bloqueia, cobra excedente ou pausa?
9. **Domínio base e DNS (`§12.8`).** Onde ficam os subdomínios das wikis por tenant?
10. **Modelos e custo-alvo por etapa (`§12.9`).** Só "modelo barato" para PRs e backfill está definido; embeddings, rerank e LLM do chat não.
11. **Hospedagem e ambientes (`§12.10`).** O repo tem Dockerfiles e scripts de deploy para `ghcr.io`/`kubectl`, mas não define onde o SaaS roda nem dev/staging/produção.
12. **Idioma da interface no v1 (`§12.11`).** A especificação exclui múltiplos idiomas, mas não diz qual é o único.
13. **Limites do plano gratuito (`§12.12`).** Além de "1 fonte, sem backfill".
