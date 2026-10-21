# Operação do CompanyKnowledge — como roda hoje, staging e GitHub App

Documento de entendimento de operação da Fase 0. Fontes: o código do CompanyBrain na `main` (commit `4e37951`) e o `ck-contexto-do-projeto.md`. Não repete a arquitetura (ver `docs/arquitetura/arquitetura-ck.md`); foca em **como subir, o que é real e o que é placeholder, e o que falta para staging e para o GitHub App**.

Regras: cada afirmação cita `caminho:linha` (repositório) ou `§N` (contexto). O que não está em nenhuma das duas fontes vai para §6, nunca como fato.

---

## 1. Como o sistema roda hoje

### 1.1 Local (sem container)

| O quê | Como | Origem |
|---|---|---|
| Web | `npm install` e `npm run dev` em `web/`; abre em `http://localhost:5173` | `web/README.md:14-18` |
| API (grafo mock) | Não há comando documentado. O único app FastAPI é `api.mock_graph.main:app`; sobe com `uvicorn api.mock_graph.main:app --port 8000`, que é a porta que o README da web assume | `api/mock_graph/main.py:7`, `web/README.md:29` |
| Conector GitHub | CLI: `python -m ingestao.github_connector.main <list-repos\|ingest-repo\|ingest-all>`, auth por PAT (`--token`) ou env | `ingestao/github_connector/main.py:20-46`, `:108` |
| Conectores Slack/Drive/Gmail | Biblioteca + CLI pontual; não há processo de serviço | `ingestao/connectors/slack/cli.py`, `ingestao/connectors/gmail/smoke_test.py` |

Verificado nesta task: `pytest api/mock_graph/test_main.py` com as dependências de `api/mock_graph/requirements.txt` → **5 testes passam**. É o único app que sobe e tem teste de ponta a ponta no repositório.

O web consome dados mock locais (`web/README.md:29`), não a API: não existe `fetch` para `localhost:8000` no caminho padrão.

### 1.2 Containers (`docker/`)

Um Dockerfile por serviço, todos com build em dois estágios (`docker/*.Dockerfile`). Não existe `docker-compose` nem manifesto Kubernetes no repositório.

| Serviço | Imagem / CMD | Estado |
|---|---|---|
| `api` | `python:3.11-slim`; `uvicorn api.main:app --host 0.0.0.0 --port 8000` (`docker/api.Dockerfile:12`) | **Quebrado.** O módulo `api.main` não existe: `api/` só tem `mock_graph/`, `README.md` e `requirements-dev.txt`. Além disso o build quebra antes: `pip install -r requirements*.txt` (`:4`) resolve para `api/requirements-dev.txt`, que só contém `-r ../ingestao/requirements-dev.txt` (`api/requirements-dev.txt:1`) — arquivo não copiado no estágio (`:3` copia apenas `api/requirements*.txt`) |
| `graph` | `python -m graph` (`docker/graph.Dockerfile:11`) | **Quebrado.** Falta `graph/__main__.py` (`graph/` só tem `.placeholder`, `README.md`, `requirements-dev.txt`) e o `pip install` tem o mesmo problema (`graph/requirements-dev.txt:1`) |
| `indexer` | `python -m indexer` (`docker/indexer.Dockerfile:11`) | **Quebrado.** Mesma ausência de `__main__.py` e mesmo problema de `pip` (`indexer/requirements-dev.txt:1`) |
| `ingestao` | `python -m ingestao` (`docker/ingestao.Dockerfile:11`) | **Quebrado.** Não há `ingestao/__main__.py`; `ingestao/__init__.py` só declara `__version__`. As dependências existem (`ingestao/requirements.txt`) |
| `web` | `node:20-alpine` → `nginx:alpine`; `npm ci` + `npm run build` (`docker/web.Dockerfile:4`, `:6`) | **Coerente.** `build` = `tsc -b && vite build` (`web/package.json:8`); `web/package-lock.json` existe. O nginx serve a SPA e faz proxy de `/api/` para `http://api:8000/` (`docker/web.nginx.conf:11-15`), então depende de um host `api` resolvível na rede |

Consequência prática: **nenhuma imagem além do `web` builda**, e o `web` só funciona em runtime se houver um `api` na mesma rede — que hoje não builda.

### 1.3 CI (GitHub Actions, `.github/workflows/`)

Dois desenhos diferentes convivem:

**a) Um workflow por serviço** (`service-{api,graph,indexer,ingestao,web}.yml`). Gatilho por `paths` do serviço (`service-api.yml:4-12`); `working-directory` do serviço (`:16`); job `lint` com `ruff check .` e `ruff format --check .` (`:29-30`); job `test` depende do lint, matriz Python 3.10/3.11/3.12, `pytest --cov` e Codecov (`:32-49`).

| Workflow | Roda o que o serviço é? |
|---|---|
| `service-ingestao.yml` | Sim: `ingestao/` tem `tests/` e `requirements-dev.txt` reais |
| `service-api.yml` | Não: `api/` não tem código no topo nem `tests/`; só `api/mock_graph/` (`api/mock_graph/test_main.py`) |
| `service-graph.yml` / `service-indexer.yml` | Não: pastas só com `.placeholder` + README; `pytest` não coleta teste algum |
| `service-web.yml` | Não: instala Python e roda `ruff`/`pytest` (`:23-30`) num projeto Node, com `cache-dependency-path: web/requirements*.txt` (`:27`) e `pip install -r requirements-dev.txt` (`:28`) — nenhum dos dois arquivos existe em `web/` (`web/package.json` é o manifesto real) |

**b) CI geral** (`ci.yml`). Ignora mudanças em `api/`, `graph/`, `indexer/` e `web/` (`:6-16`) e roda apenas os testes da raiz: `tests/` com `GDRIVE_TEST_MODE=mock` e `run_gdrive_tests.py` (`:31-36`).

Resultado: os workflows de `api`, `graph`, `indexer` e `web` são gates que não validam o serviço (e os de `web`, `graph`, `indexer`, `api` tendem a falhar por dependência/teste inexistente), enquanto o CI geral (`ci.yml`) cobre apenas os testes da raiz (Google Drive).

### 1.4 Deploy (`scripts/` + workflows)

| Etapa | O que faz | Origem |
|---|---|---|
| Gatilho staging | push na `main` tocando `ingestao/`, `indexer/`, `graph/`, `api/`, `web/`, `docker/`, `scripts/` | `.github/workflows/deploy-staging.yml:4-13` |
| Seleção de serviço | `dorny/paths-filter` com um filtro por serviço | `deploy-staging.yml:26-40` |
| Loop de deploy | `for service in ingestao indexer graph api web` e `if [ "${{ steps.changes.outputs[service] }}" = "true" ]` | `deploy-staging.yml:49-55` |
| Gatilho produção | release `published`, `environment: production`, todos os 5 serviços | `.github/workflows/deploy-prod.yml:3-10`, `:30-32` |
| Build e push | build com `-f docker/$SERVICE.Dockerfile`, push para `ghcr.io/leleocastro/companybrain` com tag do commit | `scripts/deploy-staging.sh:6`, `:11-19`; `scripts/deploy-prod.sh:6`, `:12-20` |
| "Rollout" | `echo "Deploy $SERVICE:$COMMIT_SHA to $ENV" \| kubectl apply -f - 2>/dev/null \|\| true` | `scripts/deploy-staging.sh:22`; `scripts/deploy-prod.sh:23` |

O rollout é placeholder: o `echo` produz uma linha de texto, não YAML de recursos Kubernetes, e o `|| true` engole qualquer erro. Não há `KUBECONFIG`, secret de cluster, manifesto ou cluster definido no repositório — logo o deploy não entrega nada, mesmo quando o build passa.

Bug adicional na seleção: `${{ steps.changes.outputs[service] }}` (`deploy-staging.yml:52`) usa dentro de `${{ }}` a variável `service` do `for` do shell. Expressões do GitHub Actions não leem variáveis de shell, então o nome do serviço não chega ao filtro.

---

## 2. Dependências e versões

| Camada | Versões | Origem |
|---|---|---|
| Python (imagens) | 3.11 | `docker/api.Dockerfile:1`, `:6` (idem `graph`, `indexer`, `ingestao`) |
| Python (CI) | matriz 3.10 / 3.11 / 3.12 | `.github/workflows/service-*.yml:37` |
| Raiz | `pytest>=7.0`, `google-api-python-client>=2.80`, `google-auth>=2.17`, `google-auth-oauthlib>=1.0`, `google-auth-httplib2>=0.1` | `requirements.txt:1-7` |
| `ingestao` runtime | `slack_sdk>=3.27,<4`, `pytest>=8.0`, `pytest-mock>=3.14` | `ingestao/requirements.txt:1-3` |
| `ingestao` dev/CI | `black==24.2.0`, `flake8==7.0.0`, `isort==5.13.2`, `pre-commit==3.6.0`, `pytest==8.0.0`, `pytest-asyncio==0.25.0`, `pytest-httpx==0.35.0`, `pytest-cov>=5`, `httpx==0.28.1`, `PyJWT==2.10.1`, `ruff>=0.15.0` | `ingestao/requirements-dev.txt:1-13` |
| Conector GitHub | `httpx>=0.28.0`, `PyJWT>=2.10.0` | `ingestao/github_connector/requirements.txt:1-2` |
| API mock | `fastapi>=0.100`, `uvicorn[standard]>=0.22`, `pydantic>=2.0`, `pytest>=7`, `httpx>=0.24` | `api/mock_graph/requirements.txt:1-5` |
| Node / web | Node 20; React 18.3, Vite 6, TypeScript 5.6, d3-force 3, Tailwind 3 | `docker/web.Dockerfile:1`, `web/package.json:14-31` |

Observações:
- Não há lockfile Python; só o `web` tem `package-lock.json`, usado por `npm ci` (`docker/web.Dockerfile:4`).
- `pyproject.toml` configura `black`, `isort`, `flake8` e `pytest` (`pyproject.toml:1-27`), mas **não** configura `ruff`, que é o linter do CI. Não há `requires-python` declarado para os serviços fora das imagens.
- Conviver com `pytest>=7` (raiz) e `pytest==8.0.0` (`ingestao`) é o que faz cada workflow instalar conjuntos diferentes.

---

## 3. O que é real e o que é placeholder

| Peça | Classificação | Evidência |
|---|---|---|
| SPA `web` | Real (mock de dados) | `web/src/App.tsx`, `web/package.json`; dados em `web/README.md:29` |
| `api/mock_graph` | Real, mas não é a API do produto | `api/mock_graph/main.py:7-127`; 5 testes passando |
| Conectores (GitHub, Slack, Drive, Gmail) | Real como biblioteca; sem serviço | `ingestao/connectors/`, `ingestao/github_connector/` |
| `WebhookHandler` (HMAC) | Real, mas não montado em app nenhum | `ingestao/github_connector/webhooks.py:12`, `:24` |
| `graph`, `indexer` | Placeholder | `graph/README.md`, `indexer/README.md`, `.placeholder` |
| Dockerfiles `api`/`graph`/`indexer`/`ingestao` | Placeholder (não buildam/rodam) | §1.2 |
| `scripts/deploy-*.sh` | Placeholder (rollout via `echo`) | `scripts/deploy-staging.sh:22` |
| `deploy-staging.yml` / `deploy-prod.yml` | Placeholder (sem cluster/secret; seleção inválida) | §1.4 |
| CI de `api`/`graph`/`indexer`/`web` | Placeholder (não valida o serviço) | §1.3 |
| CI `ingestao` e `ci.yml` | Real | `service-ingestao.yml`, `ci.yml:31-36` |

---

## 4. O que falta para staging

O contexto trata hospedagem e ambientes como **não definidos** (`§12.10`) e o repositório não tem cluster, manifesto ou ambiente — então staging hoje não existe. Para existir, falta:

| Área | Hoje | Falta | Origem |
|---|---|---|---|
| Onde roda | Nada no repositório | Definir provedor/cluster e como dev, staging e produção se separam | `§12.10` |
| Manifestos | Nenhum | Deployment/Service/Ingress (ou compose) por serviço, com healthcheck e réplicas | §1.4 |
| Rollout real | `echo \| kubectl apply \|\| true` | `kubectl set image`/`rollout status` (ou equivalente) com falha visível | `scripts/deploy-staging.sh:22` |
| Credenciais de deploy | Só `GITHUB_TOKEN` para o GHCR | `KUBECONFIG`/credencial do cluster como secret; proteção do environment `staging` | `deploy-staging.yml:18-23` |
| Imagens buildáveis | Só `web` builda | Corrigir entrypoints e `pip install` de `api`, `ingestao`, `graph`, `indexer` | §1.2 |
| Serviços de dados | Nada | Postgres, Redis, Qdrant e S3 disponíveis no ambiente | `§5` Armazenamento |
| Configuração | Nada | Env vars/segredos por ambiente (GitHub, LLM, Stripe no futuro) | `§5` Backend, `§5` Billing |
| Observabilidade | Nada | Logs estruturados com `tenant_id`, métricas por etapa e alertas | `§5` Observabilidade |
| Acesso e DNS | Nada | URL de staging, TLS e liberação para o QA | `§12.8`, `§12.10` |
| Dados de teste | Nada | Seed/fixtures para o QA validar os fluxos | `§9` Fase 1 |

Ordem sugerida, pela dependência real: (1) decisão de hospedagem; (2) imagens buildáveis; (3) ambiente + deploy real; (4) dados e config; (5) observabilidade; (6) acesso do QA.

---

## 5. O que falta para o GitHub App

O que já existe é só a autenticação de cliente: `AuthType.GITHUB_APP`, JWT RS256 e troca por installation token (`ingestao/github_connector/auth.py:15-18`, `:105-132`), configurada por `GITHUB_APP_ID`, `GITHUB_PRIVATE_KEY[_PATH]` e `GITHUB_INSTALLATION_ID` (`:43-52`). O resto não existe.

| Item | Hoje | Falta | Origem |
|---|---|---|---|
| Registro do App | Nada | Definir dono (conta/organização), permissões, eventos e publicação | `§12.3` |
| Instalação em 1 clique | Nada | Fluxo de instalação OAuth e escolha de repositórios | `§5` Ingestão, `§2` |
| Callback | Nada | Endpoint que recebe o `installation_id` e o vincula ao tenant | `§5` Ingestão, `§7` |
| Secret do webhook | Nada | Secret por App, guardado como segredo de ambiente | `§5` Ingestão |
| Endpoint de webhook | `WebhookHandler` verifica HMAC e trata `push`/`pull_request`/`issues`, mas não está montado em app algum | Rota pública HTTPS (`/webhooks/github`) chamando o handler | `ingestao/github_connector/webhooks.py:12`, `:24`, `:51`, `:69`, `:84` |
| Vínculo por tenant | Nada | Guardar instalação/repos por `tenant_id` com isolamento | `§7` |
| Endpoint público | Nada | API exposta em HTTPS, com URL estável para o GitHub | §4 |
| Backfill ao instalar | `GitHubIngestor` importa por `since` via CLI | Disparo na instalação, em background, com teto e filtros por plano | `ingestao/github_connector/ingestor.py:57`, `:119`; `§6` |

Dependência de sequência: o GitHub App não fecha antes de existir API com auth e `tenant_id` (`§9` Fase 1) e um endpoint público — o que depende de §4.

---

## 6. Perguntas em aberto

1. **Hospedagem e ambientes (`§12.10`).** Onde o SaaS roda em dev, staging e produção? (a) Kubernetes gerenciado, aproveitando os Dockerfiles e os scripts `kubectl`; (b) um PaaS com deploy por imagem; (c) VM única com compose para a Fase 1. Recomendação: (a) só se já houver cluster; senão (c), que é o menor caminho até o staging do QA. Impacto: todo o §4.
2. **`.github/pr-body-build.md` descreve um CI por serviço com build; o repo tem CI por serviço sem build.** Qual é o alvo — os workflows atuais são a versão final ou falta o job de build de imagem? Impacto: §1.3 e §4.
3. **O `deploy-prod.yml` dispara em `release published` sem aprovação no repositório.** A proteção do environment `production` (revisores obrigatórios) será configurada no GitHub, fora do código? Impacto: risco de deploy acidental em produção.
4. **`graph` e `indexer` viram serviços ou são removidos?** Os Dockerfiles e workflows existem, mas `§5` não os cita como serviços. Impacto: §1.2, §1.3 e §4.
5. **Registry e nomes de imagem:** `ghcr.io/leleocastro/companybrain` é fixo nos scripts (`scripts/deploy-staging.sh:6`). É o registry definitivo, e a conta `leleocastro` é a dona? Impacto: credenciais e permissões de push.
6. **URL pública e domínio da API** (para o webhook do GitHub App) — depende de `§12.8`/`§12.10`, não definidos.
7. **Segredos de terceiros** (GitHub App, LLM, Stripe): quem provisiona e em qual cofre? Nada no repositório além de `GITHUB_*` lidos por env (`ingestao/github_connector/auth.py:40-62`).
