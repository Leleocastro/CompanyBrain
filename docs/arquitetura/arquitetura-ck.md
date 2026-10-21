# Arquitetura do CompanyKnowledge — estado atual e alvo (Fase 0)

Documento de arquitetura da Fase 0. Fontes: o código do CompanyBrain na `main` (commit `4e37951`) e o `ck-contexto-do-projeto.md`.

Regras deste documento:
- Cada afirmação cita a origem: `caminho:linha` para o que existe no repositório, `§N` para o que o contexto define como alvo.
- O repositório manda para "como é hoje"; o contexto manda para "como deve ser" (`§0`).
- Divergência entre os dois é registrada, não resolvida (§6). O que não está em nenhuma das fontes é pergunta, nunca suposição.
- Decisões técnicas desta fase estão em §5 e são identificadas como decisão, não como fato do código.

---

## 1. Resumo

- O monorepo tem cinco serviços (`README.md:1`), mas só três têm código: `ingestao`, `api` e `web`. `graph` e `indexer` são placeholders (`graph/README.md`, `indexer/README.md`).
- O que existe é a **camada de conectores** (`ingestao/connectors/`), uma **API de grafo mockada em memória** (`api/mock_graph/main.py:7`) e uma **SPA que lê dados mock** (`web/src/data/mock-graph.ts`, `web/README.md`).
- Nada da fundação da Fase 1 (`§9`) está no `main`: persistência, fila, `tenant_id`, auth, GitHub App instalável, backfill, pipeline de PR, wiki, chat e Stripe.
- A base a preservar: contrato de conectores (`ingestao/connectors/base.py:10-48`), registry (`ingestao/connectors/__init__.py:11`), normalização e PII (`ingestao/normalizer.py`, `ingestao/pii.py:14`) e o conector GitHub com auth PAT/OAuth/GitHub App (`ingestao/github_connector/auth.py:15-22`) e webhook HMAC (`ingestao/github_connector/webhooks.py:24`).

**Consequência para a Fase 1:** quase tudo é construção nova; o que se aproveita é o conector GitHub e os contratos da ingestão.

---

## 2. Estado atual (main @ 4e37951)

### 2.1 Serviços e fronteiras

| Serviço | O que é hoje | Evidência |
|---|---|---|
| `ingestao` | Biblioteca de conectores (Slack, Google Drive, Gmail, GitHub), modelos, normalização, PII e registry. Não é processo executável: não há `ingestao/__main__.py`. | `ingestao/connectors/base.py:10`, `:25`; `ingestao/connectors/__init__.py:11`; `ingestao/models.py:9`; `ingestao/pii.py:14` |
| `api` | FastAPI "Mock Graph API": 5 endpoints read-only, dados seed em memória, CORS restrito a `http://localhost:5173`. | `api/mock_graph/main.py:7`, `:12`, `:88-118` |
| `web` | SPA React 18 + Vite + d3-force, visualização de grafo estilo Obsidian, alimentada por dados mock. | `web/README.md`, `web/package.json`, `web/src/data/mock-graph.ts` |
| `graph` | Placeholder (README + `.placeholder`). | `graph/README.md`, `graph/requirements-dev.txt` |
| `indexer` | Placeholder (README + `.placeholder`). | `indexer/README.md`, `indexer/requirements-dev.txt` |

**Fronteiras hoje:**
- **`web` → `api`:** HTTP em `/api/*`; o nginx faz proxy de `/api/` para `api:8000` (`docker/web.nginx.conf`). O contrato é implícito nos modelos Pydantic `Node`, `Edge`, `PaginatedNodes`, `PaginatedEdges`, `NodeDetail` (`api/mock_graph/main.py:19-47`).
- **`ingestao` → resto:** inexistente. Cada conector normaliza para `Document` (`ingestao/connectors/base.py:10`) ou `SourceDocument` (`ingestao/models.py:9`) e termina; não há fila, banco ou chamada HTTP.
- **`api` → resto:** inexistente. Sem banco, auth, tenant ou dependência externa; os dados vivem no processo (`api/mock_graph/main.py:49-77`).

### 2.2 Fluxo de dados hoje

```text
GitHub / Slack / Drive / Gmail (CLI)  →  Document normalizado  →  (fim)
web (SPA)  ──GET /api/graph/*──▶  api (dados seed em memória)
```

### 2.3 Como roda hoje

- **Local:** web com `npm install && npm run dev` em `web/` (`web/README.md`). Para a API não há comando documentado no repositório; o `CMD` do container aponta para um módulo que não existe (dívida 1 em §2.4).
- **Docker:** um Dockerfile por serviço em `docker/` (`docker/api.Dockerfile`, `docker/ingestao.Dockerfile`, `docker/graph.Dockerfile`, `docker/indexer.Dockerfile`, `docker/web.Dockerfile`).
- **Deploy:** `scripts/deploy-staging.sh` e `scripts/deploy-prod.sh` constroem e publicam em `ghcr.io/leleocastro/companybrain`; o "rollout" é `echo ... | kubectl apply -f -` (placeholder, não aplica manifesto real). Não há manifests, cluster ou ambientes definidos no repositório. Workflows de deploy: `.github/workflows/deploy-staging.yml`, `.github/workflows/deploy-prod.yml`.
- **CI:** um workflow por serviço (`.github/workflows/service-*.yml`) com `ruff check`, `ruff format --check` e `pytest`; mais `.github/workflows/ci.yml`, que roda `tests/` com `GDRIVE_TEST_MODE=mock`.

### 2.4 Dívidas verificáveis do estado atual

Registradas aqui; **não corrigidas neste PR** (cards `docs` não alteram código).

1. `docker/api.Dockerfile:12` executa `uvicorn api.main:app`, mas o único módulo FastAPI existente é `api/mock_graph/main.py`. Decisão em §5.2.
2. `docker/ingestao.Dockerfile` executa `python -m ingestao`, e não existe `ingestao/__main__.py`. O mesmo padrão aparece em `docker/graph.Dockerfile` e `docker/indexer.Dockerfile` (`python -m graph` / `python -m indexer`), cujas pastas só têm `.placeholder`.
3. `.github/workflows/service-web.yml` roda Python (`ruff`, `pytest`) em `web/`, mas `web/` é um projeto Node (`web/package.json`) e não tem `requirements-dev.txt`. O job não valida o que o serviço é.
4. `scripts/deploy-staging.sh` e `scripts/deploy-prod.sh` não fazem rollout real (§2.3).
5. A API não expõe nenhum webhook: o handler `WebhookHandler` existe em `ingestao/github_connector/webhooks.py:12`, mas não está montado em nenhuma aplicação.

---

## 3. Arquitetura-alvo (`§5`)

| Camada | O que o contexto define | Origem |
|---|---|---|
| Backend | FastAPI multi-tenant; todo request carrega `tenant_id`; auth dupla (API key e sessão); rate limit por tenant no Redis | `§5` Backend |
| Ingestão | GitHub App (instalação em 1 clique via OAuth, webhooks de PR), upload de documentos, `POST /v1/ingest`, fila assíncrona Redis para picos e backfill | `§5` Ingestão |
| Pipeline | LiteLLM como gateway; PR vira resumo estruturado em Markdown versionado; documentos viram Markdown; crons diário e semanal; verificação Jev com bandas de confiança; fila de revisão humana para a banda do meio | `§5` Pipeline |
| Armazenamento | Postgres (tenants, usuários, documentos, regras, assinaturas, uso, auditoria), Qdrant (embeddings isolados por tenant), Redis (filas, cache, uso), S3 (originais e builds da wiki) | `§5` Armazenamento |
| Wiki | Build estático por tenant em subdomínio próprio, busca full-text + semântica, graph view, versionamento e citações de origem | `§5` Wiki |
| Chat | Motor RAG único (Qdrant + rerank + citações), duas superfícies: embutida na wiki e standalone com histórico e feedback | `§5` Chat |
| MCP e API | REST documentada; servidor MCP via HTTP com API key no v1 (`search_memory`, `get_document`, `ask`); OAuth no MCP só no enterprise | `§5` MCP e API pública |
| Billing | Stripe: base fixa + excedente medido, portal embutido, medição por evento | `§5` Billing |
| Painel do cliente | Fontes, API keys, uso com alertas em 70%/90%, trava de gasto, pacotes, convites | `§5` Painel do cliente |
| Admin do fundador | Tenants com saúde e custo de tokens por workspace, status da pipeline, alertas, kill switch, impersonação | `§5` Admin do fundador |
| Observabilidade | Logs estruturados sempre com `tenant_id`; métricas por etapa; alertas proativos | `§5` Observabilidade |

### 3.1 Fluxo-alvo de uma PR (síntese de `§5`, `§6`, `§9`)

```text
PR mergeado no GitHub
  → webhook assinado chega na API
  → API valida HMAC e enfileira no Redis
  → consumidor da fila chama o LiteLLM (modelo barato)
  → Markdown versionado + registro no Postgres
  → indexação no Qdrant (chunks por tenant)
  → rebuild da wiki do tenant
  → página publicada com citação da origem (repo, PR, arquivo)
```

O contexto não nomeia o processo que consome a fila nem onde o Markdown é versionado; ambos estão em §6.

---

## 4. Alvo vs. hoje — lacunas da Fase 1 (`§9`)

| Área da Fase 1 | Hoje | Lacuna | Card |
|---|---|---|---|
| Persistência | Nada | Postgres e Redis com migrations | CK-3 |
| Multi-tenant | Nada (`api/mock_graph` não tem `tenant_id`) | `tenant_id` no modelo e isolamento em banco, vetores e storage (`§7`) | CK-4 |
| Auth | Nada | API key (hash e escopos) + sessão do painel | CK-5 |
| Rate limit | Nada | Limite por tenant no Redis | CK-6 |
| GitHub App | Auth PAT/OAuth/GitHub App no cliente (`ingestao/github_connector/auth.py:15-22`), sem instalação/callback | Instalação, callback e vínculo por tenant | CK-7 |
| Webhook → fila | Handler HMAC isolado (`webhooks.py:24`), não montado | Endpoint na API + enfileiramento no Redis | CK-8 |
| Backfill | `GitHubIngestor` importa commits/PRs/issues por `since` (`ingestao/github_connector/ingestor.py:57`, `:119`) | Backfill por plano, em background, com teto e filtros (`§6`) | CK-9 |
| Pipeline de PR | Nada | Resumo estruturado em Markdown versionado | CK-10 |
| Wiki | Nada; `web` mostra grafo mock | Wiki por tenant com citações | CK-11 |
| Chat | Nada | RAG nas duas superfícies | CK-12 |
| Stripe | Nada | Base fixa e portal de cobrança | CK-13 |

Fora da Fase 1: documentos/`/v1/ingest`, crons e Jev, medição, painel, admin (`§9` Fase 2); MCP e API pública, demo e landing (Fase 3). Os conectores Slack/Drive/Gmail existentes ficam como base, mas a especificação coloca conectores em "Depois" (`§9`).

---

## 5. Decisões desta fase

### 5.1 Onde vivem documentação e skills

Decisão: tudo em `docs/`, na raiz do repositório, com uma pasta por tipo:

| Pasta | Conteúdo | Quem escreve |
|---|---|---|
| `docs/produto/` | Visão de produto, roadmap e critérios de fase | po |
| `docs/arquitetura/` | Arquitetura, "estado atual" por área, ADRs (`docs/arquitetura/adr/`) | tech-lead, dev-backend, dev-frontend, devops |
| `docs/skills/` | Skills dos agentes, um arquivo Markdown por skill | reviewer, qa (e demais papéis quando criarem skill) |

Motivo:
- Não existe pasta de documentação no `main` hoje; `docs/` na raiz mantém todo o material fora dos diretórios de serviço e não interfere em build de nenhum serviço (`docker/*.Dockerfile` copiam só a pasta do serviço).
- O `docs/produto/` criado pelo po em CK-1 já está sob `docs/` e **permanece onde está** — mover não agrega e atrasaria o PR #14.
- O pre-commit já formata Markdown com prettier (`.pre-commit-config.yaml`), então `docs/` entra no padrão existente sem configuração nova.
- Skills ficam no repositório, versionadas, e não são vinculadas a agentes no Multica (decisão do fundador, não desta fase).

Nomes dos artefatos de entendimento desta fase:
- dev-backend: `docs/arquitetura/backend-estado-atual.md`
- dev-frontend: `docs/arquitetura/frontend-estado-atual.md`
- devops: `docs/arquitetura/operacao-estado-atual.md`
- reviewer: `docs/skills/checklist-revisao.md`
- qa: `docs/skills/plano-de-testes.md`

### 5.2 Entrypoint da API hoje

Decisão: o entrypoint oficial do que existe hoje é `api.mock_graph.main:app` — é o único módulo FastAPI no repositório (`api/mock_graph/main.py:7`). `docker/api.Dockerfile:12` está incorreto e deve ser corrigido no início da Fase 1, junto do primeiro card que tocar a API (CK-3/CK-5). Este PR é `docs` e não altera código.

### 5.3 O que preservar do que existe

- **Preservar:** contrato `BaseConnector`/`Document` e o registry da ingestão (`ingestao/connectors/base.py:25`, `ingestao/connectors/__init__.py:11`), normalização e PII (`ingestao/normalizer.py`, `ingestao/pii.py:14`), auth e webhook do GitHub (`ingestao/github_connector/auth.py:22`, `webhooks.py:24`). É a única parte alinhada ao alvo.
- **Substituir, não evoluir:** a "Mock Graph API" não é a API do produto (`§5` Backend exige auth, `tenant_id` e rate limit que ela não tem). O contrato `/api/graph/*` serve hoje só para a SPA (`web/src/data/mock-graph.ts`); a API da Fase 1 nasce com os cards CK-3..CK-6 e o mock fica como referência até a troca.
- **Fora da Fase 1:** `graph` e `indexer` como serviços separados não aparecem em `§5`; o alvo descreve o pipeline dentro do backend e o armazenamento em Postgres/Qdrant/S3. Manter as pastas não custa nada, mas não são dependência da Fase 1.

---

## 6. Perguntas em aberto

### Ao fundador (produto, contrato, infraestrutura)

1. **Plataforma "que já existe" (`§1`, `§12.1`).** O `main` só tem conectores, API mock e web de grafo. Onde está o código da plataforma que "já opera hoje" — fora do CompanyBrain? A Fase 1 parte do zero nessas peças?
2. **Onde vive o Markdown versionado no SaaS (`§12.4`).** `§5` cita "Markdown versionado", documentos no Postgres e originais no S3, sem definir o modelo. Opções: (a) repositório Git por tenant — mais próximo do artigo (`§10`) e dá histórico de graça; (b) Postgres com versionamento por linha — menos peças, sem Git; (c) S3 com versões — simples, busca pior. Recomendação: (a) para a wiki gerada, com Postgres como índice. Impacto: define o modelo de dados e o build da wiki (CK-10, CK-11).
3. **GitHub App (`§12.3`).** Quais permissões e eventos? Conta pessoal ou organização? Publicado no Marketplace? Impacto: CK-7 e CK-8.
4. **Hospedagem e ambientes (`§12.10`).** O repo tem Dockerfiles e deploy para `ghcr.io`/`kubectl`, mas não define onde o SaaS roda. Impacto: staging do QA e deploy (CK-3 em diante).
5. **Modelos e custo-alvo por etapa (`§12.9`).** Só "modelo barato" para PRs e backfill está definido; embeddings, rerank e LLM do chat não. Impacto: pipeline (CK-10) e chat (CK-12).
6. **Domínio base e DNS (`§12.8`).** Onde ficam os subdomínios das wikis por tenant. Impacto: CK-11.

### Técnicas (resolver no refinamento dos cards)

7. **Contrato `/api/graph/*`:** é contrato interno da SPA ou API pública? Hoje só o `web` consome, com dados mock (`web/src/data/mock-graph.ts`).
8. **Endpoint de webhook:** a API expõe `/webhooks/github` e usa o secret da GitHub App? O `WebhookHandler` existe, mas não está montado (`ingestao/github_connector/webhooks.py:12`).
9. **Limpeza dos placeholders:** `graph`/`indexer` e seus Dockerfiles serão removidos ou viram o pipeline? O alvo não os cita (`§5`).

---

## 7. Premissas

- `docs/` na raiz com `produto/`, `arquitetura/` e `skills/` (§5.1); `docs/produto/` do po não é movido.
- O entrypoint atual da API é `api.mock_graph.main:app`; o Dockerfile está errado e será corrigido na Fase 1 (§5.2).
- Este documento fotografa a `main` em `4e37951`; branches de trabalho (incluindo o PR #14 do po) não são tratadas como existentes.
- Os conectores Slack/Drive/Gmail são base pronta, não escopo da Fase 1 (`§9`).
- Dúvidas de conteúdo desta fase não bloqueiam: estão em §6 e o po consolida no fim da Fase 0.
