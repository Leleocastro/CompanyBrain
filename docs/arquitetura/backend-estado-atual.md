# Backend do CompanyKnowledge — estado atual e lacunas (Fase 0)

Documento de entendimento do backend. Fotografa o código do CompanyBrain na `main` (`4e37951`; `ee718ce` só acrescenta `docs/produto/visao-do-produto.md`, então o código é o mesmo) e compara com o alvo do `ck-contexto-do-projeto.md`.

Regras: `caminho:linha` para o repositório, `§N` para o contexto. Divergência é registrada, não resolvida; o que não está em nenhuma das duas fontes vai para §5. O desenho de arquitetura da fase está em `docs/arquitetura/arquitetura-ck.md` (PR #15); aqui o foco é o backend que existe.

## 1. Como o backend funciona hoje

### 1.1 Serviços

| Serviço | O que é hoje | Evidência |
|---|---|---|
| `api` | FastAPI "Mock Graph API" com dados seed em memória | `api/mock_graph/main.py:7`, `:49-77` |
| `ingestao` | biblioteca de conectores; não é processo executável | `ingestao/__init__.py`, ausência de `__main__.py` |
| `graph` | placeholder | `graph/README.md`, `graph/.placeholder` |
| `indexer` | placeholder | `indexer/README.md`, `indexer/.placeholder` |
| `web` | SPA que importa dados mock locais | `web/src/App.tsx:5` |

### 1.2 API (`api/mock_graph`)

- App criado em `api/mock_graph/main.py:7`; CORS liberado só para `http://localhost:5173` (`:10-16`).
- Contrato implícito nos modelos Pydantic `Node`, `Edge`, `PaginatedNodes`, `PaginatedEdges`, `NodeDetail` (`:19-47`).
- Dados em memória: 20 nós com embedding aleatório e 30 arestas, gerados no import (`:49-77`).
- Cinco endpoints, todos `GET` e read-only (`:88-127`): `/api/health` (`:88`), `/api/graph/nodes` (`:92`), `/api/graph/edges` (`:98`), `/api/graph/search` (`:104`), `/api/graph/node/{node_id}` (`:112`).
- Sem auth, `tenant_id`, banco, fila ou chamada à ingestão; o estado morre no restart. `api/` não tem `__init__.py` (import por namespace, como em `api/mock_graph/test_main.py:2`).
- A SPA não consome a API: importa `web/src/data/mock-graph.ts` direto (`web/src/App.tsx:5`). O proxy `/api/` do nginx existe (`docker/web.nginx.conf:11-12`), mas hoje só serve o mock.

### 1.3 Ingestão

**Contrato e registry**
- `Document` normalizado: `ingestao/connectors/base.py:10-22`.
- `BaseConnector` (`:25`) exige `authenticate`, `list_files`, `download`, `extract_metadata` (`:28-46`); `ingest` na base só levanta `NotImplementedError` (`:48-50`).
- Registry em `ingestao/connectors/__init__.py`: decorator `register` (`:11`), factory `get_connector` (`:19`), `list_sources` (`:28`).
- O registry é vazio até o módulo do conector ser importado: `list_sources()` devolve `{}`; só depois de importar `google_drive` (`google_drive/client.py:14`, `:46`) aparece `google_drive`. Não há auto-discovery.

**Modelos divergentes (não há um modelo canônico)**
- `base.Document` (`ingestao/connectors/base.py:10`), usado pelo Drive.
- `github_connector/normalizer.py:9` — `Document` com `id_origem`, `channel`, `excerpt`.
- `slack/normalize.py:8` — `Document` com `thread_ts`, `attachments`.
- `ingestao/models.py:9` — `SourceDocument`, definido e **não usado** em nenhum lugar do repo.
- Gmail devolve `dict` (`ingestao/connectors/gmail/parser.py:6`).

**Normalização e PII**
- `compute_sha256` (`ingestao/normalizer.py:8`) e `safe_timestamp` (`:12`).
- `redact_pii` (`ingestao/pii.py:14`), `has_pii` (`:21`); padrões de e-mail, telefone e SSN (`:7-11`).
- Só o normalizer do Drive aplica PII (`ingestao/connectors/google_drive/normalizer.py:23`); GitHub e Slack não.

**GitHub (`ingestao/github_connector/`)**
- Auth: `AuthType` PAT/OAuth/GitHub App (`auth.py:15-18`); `AuthConfig.from_env` (`:39`); `GitHubAuth` (`:80`); JWT da App (`:105-132`); troca de código OAuth (`:134-152`); PAT (`:94-95`).
- Client HTTP async (`client.py:64`), paginação (`:80`), repos (`:111`), commits (`:143`), PRs (`:173`), issues (`:195`; exclui PRs em `:197`).
- Ingestion: `GitHubIngestor` (`ingestor.py:29`); `ingest_repo` (`:57`) roda commits/PRs/issues em paralelo (`:65-70`); `ingest_all_repos` (`:119`) com semáforo (`:39`); erro por repo em `IngestResult.errors` (`:17-26`).
- Normalizer: `normalize_commit` (`normalizer.py:35`), `normalize_pull_request` (`:56`), `normalize_issue` (`:78`); excerpt de 512 chars (`:26`) e sha256 (`:22`).
- Webhook: `WebhookHandler` (`webhooks.py:12`), HMAC (`:24-28`), dispatch (`:30-46`), `process_ping`/`process_push`/`process_pull_request`/`process_issues` (`:48-98`). **Não está montado em nenhuma aplicação**; só é exercitado nos testes.
- CLI: `main.py:20-77` com `list-repos`, `ingest-repo`, `ingest-all` (`:26`).

**Drive, Gmail, Slack**
- Drive é o único conector completo do contrato: `GoogleDriveConnector(BaseConnector)` (`google_drive/client.py:47`), `@register("google_drive")` (`:46`), `list_files` (`:152`), `download` (`:210`), `extract_metadata` (`:264`), `ingest` (`:288`), mock por `GDRIVE_TEST_MODE=mock` (`:85`).
- Gmail tem OAuth (`gmail/auth.py`), client (`gmail/client.py:12`) e parser que devolve `dict` (`gmail/parser.py:6`); entra em modo mock sozinho sem credenciais (`gmail/client.py:20-21`, `gmail/auth.py:31-32`).
- Slack usa `slack_sdk` (`slack/client.py:11`), com canais (`channels.py:4`), threads (`threads.py:4`), normalização (`normalize.py:41`) e CLI (`cli.py:58`).

### 1.4 Fluxo de dados hoje

```text
CLI GitHub/Slack ─┐
Drive (registry) ─┼─▶ Document ou dict em memória ─▶ fim (nada persiste)
Gmail ────────────┘
web (mock local) ───▶ api/mock_graph (seed em memória)
```

Nenhum conector grava em banco, fila ou object storage; a `api` não chama a `ingestao`; não existe `tenant_id` em nenhum arquivo `.py` do repo. O webhook existe isolado (§1.3).

### 1.5 Persistência, observabilidade e segurança

- As dependências não incluem Postgres, Qdrant, Redis, S3, Stripe, LiteLLM nem MCP (`requirements.txt`, `ingestao/requirements*.txt`, `api/mock_graph/requirements.txt`).
- Log é o `logging` padrão, no CLI do GitHub (`github_connector/main.py:13-17`), sem `tenant_id`.
- `§7` exige isolamento por `tenant_id` em banco, vetores e storage, API keys com hash e escopos, exclusão e exportação por workspace. Nada disso existe no código.

## 2. Como rodar e testar

Pré-requisitos: Python 3.11 nos containers (`docker/*.Dockerfile:1`) e matriz 3.10–3.12 no CI (`.github/workflows/service-ingestao.yml:37`).

Comandos verificados em 2026-10-21 (raiz do repo):

```bash
pip install -r requirements.txt
# deps de teste da ingestão, com os pins corrigidos (ver 2.1, item 3)
pip install "pytest>=8.2,<9" pytest-asyncio==0.25.0 pytest-httpx==0.35.0 \
  pytest-mock httpx==0.28.1 PyJWT==2.10.1 "slack_sdk>=3.27,<4"

python -m pytest -q ingestao api                  # 98 passed
GDRIVE_TEST_MODE=mock python -m pytest -q tests/  # 24 passed
python ingestao/connectors/gmail/smoke_test.py    # 5 PASS
```

- `pytest` puro na raiz roda **83** testes: o `testpaths` do `pyproject.toml:25` só cobre `ingestao/tests`, `ingestao/github_connector/tests` e `tests/` (e cita `api/tests`, `graph/tests`, `indexer/tests`, que não existem).
- CLIs funcionam: `python -m ingestao.github_connector.main --help` (`github_connector/main.py:108-109`) e `python -m ingestao.connectors.slack.cli --help` (`slack/cli.py:84-85`).
- Entrypoint real da API: o único `FastAPI(...)` do repo é `api/mock_graph/main.py:7`, usado pelos testes em `api/mock_graph/test_main.py:2`. Não há comando de execução documentado no repo (`api/README.md` só tem o título).

### 2.1 O que está quebrado hoje (verificado)

| # | Onde | Problema |
|---|---|---|
| 1 | `docker/api.Dockerfile:4` | build falha: `api/requirements-dev.txt:1` aponta para `../ingestao/requirements-dev.txt`, que não é copiado (o `COPY` em `:3` só pega `api/requirements*.txt`). Erro observado: `Could not open requirements file: ../ingestao/requirements-dev.txt`. |
| 2 | `docker/api.Dockerfile:12` | `CMD` executa `api.main:app`, módulo que não existe; o único app é `api/mock_graph/main.py:7`. |
| 3 | `docker/ingestao.Dockerfile:4` | build falha: `pytest==8.0.0` (`ingestao/requirements-dev.txt:5`) conflita com `pytest-asyncio==0.25.0` (`:6`, exige `pytest>=8.2,<9`). Mesmo erro com `pip` e com `uv`. |
| 4 | `docker/ingestao.Dockerfile:11` | `CMD` é `python -m ingestao`, mas não existe `__main__.py` em nenhum diretório do repo. |
| 5 | `.github/workflows/service-api.yml:28`, `.github/workflows/service-ingestao.yml:28` | ambos instalam `requirements-dev.txt` e param no conflito do item 3 (api herda via `api/requirements-dev.txt:1`). |
| 6 | `.github/workflows/service-api.yml:16`, `:46` | `pytest` roda com `working-directory: api`, mas `api/mock_graph/test_main.py:2` importa `api.mock_graph` e `api/` não tem `__init__.py`: `ModuleNotFoundError: No module named 'api'` (o mesmo teste passa rodando da raiz). |
| 7 | `.github/workflows/service-api.yml:29-30` | `ruff check .` e `ruff format --check .` falham em `api/` (14 erros e 2 arquivos a reformatar, com `ruff 0.17.1`; o repo não tem config de ruff, `pyproject.toml:1-22` só define black/isort/flake8). |
| 8 | `.github/workflows/service-web.yml:25-30` | job Python (`setup-python`, `requirements-dev.txt`, `ruff`, `pytest`) em `web/`, que é projeto Node (`web/package.json`) e não tem `requirements-dev.txt`. |
| 9 | `scripts/deploy-staging.sh:22` | o "rollout" é `echo ... \| kubectl apply -f -`, que não aplica manifesto real; `scripts/deploy-prod.sh` repete o padrão. |

## 3. Convenções do código

- Python 3.11; contratos em `dataclass` (`connectors/base.py:9`, `github_connector/normalizer.py:8`); `httpx.AsyncClient` para HTTP (`github_connector/client.py:64`); `from __future__ import annotations` nos módulos do GitHub (`auth.py:1`).
- Configuração por variável de ambiente (`auth.py:39-62`), com `repr=False` em token e chave privada (`auth.py:28`, `:31`) — segredos não vão para log.
- Testes junto do código (`github_connector/tests/`, `gmail/tests/`) e também na raiz (`tests/`); `python_files = ["test_*.py", "*_test.py"]` (`pyproject.toml:27`).
- Lint: black 88 / isort perfil black / flake8 88 (`pyproject.toml:1-22`), pre-commit com black, isort, flake8, prettier e eslint (`.pre-commit-config.yaml:12-40`); o CI usa `ruff` (`service-*.yml:29-30`), sem configuração de ruff no repo.
- Não há camadas (router/service/repository), migrations, injeção de dependência nem suíte de integração — a única convenção a herdar é o contrato de conectores e o registry.

## 4. O que falta para o alvo (`§5`)

| Área do `§5` | Hoje | Lacuna para o alvo |
|---|---|---|
| Backend | API mock sem auth nem tenant (`api/mock_graph/main.py:88-127`) | FastAPI multi-tenant com `tenant_id` em todo request, auth dupla (API key e sessão) e rate limit por tenant no Redis (`§5` Backend; `§7`) |
| Ingestão — GitHub App | auth App no cliente (`auth.py:15-18`), sem instalação nem callback | instalação em 1 clique, escolha de repositórios e vínculo por tenant (`§5` Ingestão; `§12.3`) |
| Ingestão — fila | nada; ingestão é síncrona na CLI (`ingestor.py:57`) | fila Redis entre chegada e processamento, incluindo backfill (`§5` Ingestão; `§9` Fase 1) |
| Ingestão — webhook | HMAC pronto e não montado (`webhooks.py:12`) | endpoint na API e enfileiramento do evento (`§5` Ingestão) |
| Ingestão — documentos e `/v1/ingest` | nada; Drive/Gmail/Slack são conectores, não endpoints | upload de PDF/Markdown/TXT no painel e `POST /v1/ingest` (`§5` Ingestão; `§9` Fase 2) |
| Pipeline LiteLLM | nada | PR → Markdown versionado, documentos → Markdown, crons diário/semanal, verificação Jev por bandas e fila de revisão (`§5` Pipeline; `§9` Fase 2) |
| Armazenamento | nada | Postgres, Qdrant por tenant, Redis e S3 (`§5` Armazenamento; `§7`) |
| Wiki e chat | nada (`web` é grafo mock, `web/src/App.tsx:5`) | wiki estática por tenant e RAG nas duas superfícies (`§5` Wiki, Chat) |
| MCP e API pública | nada; nem REST documentada | REST documentada e MCP via HTTP com API key, ferramentas `search_memory`, `get_document`, `ask` (`§5` MCP e API pública; `§9` Fase 3) |
| Billing | nada | Stripe: base fixa, medição por evento e portal (`§5` Billing; `§9` Fase 1 e 2) |
| Admin e observabilidade | `logging` padrão sem `tenant_id` (`github_connector/main.py:13-17`) | logs com `tenant_id`, métricas por etapa, alertas e admin por tenant (`§5` Admin do fundador, Observabilidade) |

### 4.1 O que preservar

- Contrato `BaseConnector`/`Document` e registry (`connectors/base.py:25`, `connectors/__init__.py:11`).
- Normalização e PII (`normalizer.py`, `pii.py:14`), hoje aplicadas só no Drive.
- Auth e webhook do GitHub (`github_connector/auth.py:22`, `webhooks.py:24`).
- O conector Drive é a única implementação completa do contrato (`google_drive/client.py:47`); serve de referência para os demais.

## 5. Perguntas em aberto

1. **Conectores não-GitHub no v1:** Drive, Gmail e Slack existem no repo, mas `§9` coloca "conectores (Slack, Drive, Notion)" em "Depois". Eles entram no v1 como fontes ou ficam fora até a Fase 3?
2. **Modelo canônico de documento:** qual vence — `base.Document` (`connectors/base.py:10`), o do GitHub (`github_connector/normalizer.py:9`), o do Slack (`slack/normalize.py:8`) ou `SourceDocument` (`ingestao/models.py:9`)? Este último diz ser "payload forwarded to the indexer agent" (`models.py:10`), mas não é usado e `indexer/` é placeholder (`indexer/README.md`).
3. **PII:** só o Drive redige (`google_drive/normalizer.py:23`). A redação é na entrada ou na geração? `§7` exige isolamento e LGPD, mas não define onde redigir; o normalizer do GitHub não tem PII (`github_connector/normalizer.py`).
4. **Registry:** registro por import explícito (como hoje, `google_drive/client.py:46`) ou auto-discovery? `§5` não define; `get_connector` quebra com registry vazio (`connectors/__init__.py:21-25`).
5. **Entrypoint da API:** onde nasce a API da Fase 1 — em `api/main.py` (corrigindo `docker/api.Dockerfile:12`) ou evoluindo `api.mock_graph`? O `arquitetura-ck.md` §5.2 decide o entrypoint atual, não o da Fase 1.
6. **Consumidor da fila:** `§5` fala em fila Redis, mas não nomeia o processo que consome (o mesmo backend? worker separado?). O `Dockerfile` de `ingestao` sugere um processo próprio, que hoje não existe (`docker/ingestao.Dockerfile:11`).
7. **Versão de Python:** containers usam 3.11 (`docker/*.Dockerfile:1`) e o CI testa 3.10–3.12 (`service-ingestao.yml:37`); o `pyproject.toml` não declara a versão do runtime (só `target-version` do black, `:3`). Qual é a versão-alvo do backend?
8. **Credenciais por tenant:** instalação do GitHub App e tokens OAuth precisam ser guardados por tenant; `§5`/`§7` definem o isolamento, mas não onde armazenar (Postgres? secret manager?).
