# Skill do devops — subir, publicar e tratar segredos

Procedimento do devops do CompanyKnowledge para todo card que toque infraestrutura. Vale o repositório CompanyBrain; o `ck-contexto-do-projeto.md` descreve o alvo e pode divergir (`ck-contexto-do-projeto.md:7`, `§0`). Cada item cita a origem (`caminho:linha` ou `§N`). O que não tem origem está nas "Perguntas em aberto".

## 1. Subir local

- Web: `cd web && npm install && npm run dev` → `http://localhost:5173` (`web/README.md:13-18`).
- API: `uvicorn api.mock_graph.main:app --port 8000` — único app FastAPI e a porta que o web assume (`api/mock_graph/main.py:7`, `web/README.md:29`).
- O web usa mock local por padrão; não chama `localhost:8000` (`web/README.md:29`).
- Conector GitHub por CLI: `python -m ingestao.github_connector.main <list-repos|ingest-repo|ingest-all>`, auth por PAT (`ingestao/github_connector/main.py:20-46`, `:108`).
- Slack/Drive/Gmail: biblioteca + CLI pontual, sem processo de serviço (`ingestao/connectors/slack/cli.py`, `ingestao/connectors/gmail/smoke_test.py`).
- Containers: um Dockerfile por serviço em `docker/`; **não existe** `docker-compose` nem manifesto Kubernetes (`docker/*.Dockerfile`; `docs/arquitetura/operacao-estado-atual.md:26`).
- **Nenhuma das cinco imagens builda hoje**: `pip install -r requirements*.txt` (`docker/api.Dockerfile:4`, `docker/ingestao.Dockerfile:4`) e `npm ci` (`docker/web.Dockerfile:4`) falham (`docs/arquitetura/operacao-estado-atual.md:36`).
- Mesmo buildando, `api`/`graph`/`indexer`/`ingestao` não têm entrypoint: `api.main:app` (`docker/api.Dockerfile:12`) e `python -m ingestao` (`docker/ingestao.Dockerfile:11`) não existem — `api/main.py`, `graph/__main__.py` e `ingestao/__main__.py` estão ausentes (`docs/arquitetura/operacao-estado-atual.md:30-33`).
- Só o `web` é coerente: nginx serve a SPA com fallback e faz proxy `/api/` → `http://api:8000/` (`docker/web.nginx.conf:7-15`).

## 2. Publicar

**O que existe hoje** (tudo placeholder):

- Staging dispara em push na `main` tocando `ingestao/`, `indexer/`, `graph/`, `api/`, `web/`, `docker/`, `scripts/` (`.github/workflows/deploy-staging.yml:3-13`).
- Seleção por `dorny/paths-filter` com um filtro por serviço (`deploy-staging.yml:26-40`).
- Loop `for service in ingestao indexer graph api web` (`deploy-staging.yml:49-55`).
- Bug na seleção: `${{ steps.changes.outputs[service] }}` usa dentro da expressão a variável `service` do shell, que o GitHub Actions não lê (`deploy-staging.yml:52`; `docs/arquitetura/operacao-estado-atual.md:68`).
- Prod: release `published`, `environment: production`, todos os cinco serviços (`.github/workflows/deploy-prod.yml:3-10`, `:30-32`).
- Build/push: `-f docker/$SERVICE.Dockerfile` para `ghcr.io/leleocastro/companybrain`, tag do commit e `latest` (`scripts/deploy-staging.sh:6`, `:11-19`; `scripts/deploy-prod.sh:6`, `:12-20`).
- "Rollout" é `echo "Deploy ..." | kubectl apply -f - 2>/dev/null || true` — não é YAML de recurso e o `|| true` engole o erro (`scripts/deploy-staging.sh:22`).
- Sem `KUBECONFIG`, secret de cluster ou manifesto no repositório: o deploy não entrega nada mesmo com build verde (`docs/arquitetura/operacao-estado-atual.md:66`).
- Merge de card `docs` **não** dispara deploy: `docs/**` não está nos `paths` (`deploy-staging.yml:6-13`).
- CI que roda de verdade: `ci.yml` (testes da raiz, Google Drive) e `service-ingestao.yml`; os de `api`/`graph`/`indexer`/`web` não validam o serviço (`.github/workflows/ci.yml:6-16`, `:31-36`; `docs/arquitetura/operacao-estado-atual.md:53`).

**Alvo — o que falta para staging** (não implementar sem card; registrar a lacuna):

- Definir provedor/cluster e separação dev/staging/produção (`§12.10`, `ck-contexto-do-projeto.md:281`).
- Corrigir os cinco builds e os entrypoints antes de qualquer deploy (`docs/arquitetura/operacao-estado-atual.md:119`).
- Manifestos (Deployment/Service/Ingress) ou compose por serviço, com healthcheck e réplicas (`docs/arquitetura/operacao-estado-atual.md:116`).
- Rollout real com falha visível, tipo `kubectl set image` + `rollout status` (`docs/arquitetura/operacao-estado-atual.md:117`).
- Credencial de cluster como secret e environment `staging` protegido; hoje só há `GITHUB_TOKEN` para o GHCR (`deploy-staging.yml:18-23`, `:47`).
- Postgres, Redis, Qdrant e S3 no ambiente (`§5` Armazenamento, `ck-contexto-do-projeto.md:98-102`).
- Env vars/segredos por ambiente e logs estruturados com `tenant_id` (`§5` Backend/Observabilidade, `ck-contexto-do-projeto.md:78`, `:126-127`).
- URL de staging, TLS e liberação para o QA (`§12.8`, `ck-contexto-do-projeto.md:279`).
- Ordem pela dependência real: hospedagem → imagens → ambiente/deploy → dados → observabilidade → acesso do QA (`docs/arquitetura/operacao-estado-atual.md:126`).

## 3. Segredos e webhooks

- **R14: nunca escrever chave, token ou senha em código, card, PR ou log.** Só o nome da variável e onde ela é consumida. `.env` está no `.gitignore` (`.gitignore:2`) e o pre-commit tem `detect-private-key` (`.pre-commit-config.yaml:11`).
- GitHub App por env: `GITHUB_APP_ID`, `GITHUB_PRIVATE_KEY` ou `GITHUB_PRIVATE_KEY_PATH`, `GITHUB_INSTALLATION_ID` (`ingestao/github_connector/auth.py:43-52`).
- PAT por `GITHUB_TOKEN` (`auth.py:40-41`); OAuth por `GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET` (`auth.py:58-62`).
- Não imprimir credencial: `private_key` e `personal_token` são `repr=False` (`auth.py:28`, `:31`). Mantenha assim em qualquer mudança.
- No Actions, `GITHUB_TOKEN` é emitido pelo runner — não criar secret com esse nome (`deploy-staging.yml:47`).
- Webhook: `WebhookHandler(secret)` valida `X-Hub-Signature-256` com HMAC-SHA256 e `compare_digest` antes de processar (`ingestao/github_connector/webhooks.py:12-33`). O secret vem de fora, nunca do código (`:13`).
- O `WebhookHandler` existe mas **não está montado em app nenhum** — falta rota que receba o evento (`docs/arquitetura/operacao-estado-atual.md:99`, `:140`).
- Alvo: secret por App guardado como segredo de ambiente e verificação HMAC na borda (`ck-contexto-do-projeto.md:212`, `§10`; `docs/arquitetura/operacao-estado-atual.md:139`).
- Alvo: callback que recebe o `installation_id` e vincula ao tenant — rota e vínculo não definidos (`docs/arquitetura/operacao-estado-atual.md:138`; `§12.3`, `ck-contexto-do-projeto.md:274`).
- Sequência: webhook/callback só fecham depois de API com auth e `tenant_id` (`§9` Fase 1) e de URL pública (`§12.8`) (`docs/arquitetura/operacao-estado-atual.md:144`).

## 4. Antes do PR

- Card `in_progress`; branch própria. Card `docs`: branch `docs/<assunto>`, sem a KEY no título, no corpo (`Closes`/`Fixes`/`Resolves`) nem na branch (`docs/skills/checklist-revisao.md:10-12`).
- Diff só no escopo: card `docs` não altera código (`docs/skills/checklist-revisao.md:13`).
- Evidência no PR: saída do comando/build/teste que sustenta a afirmação (`docs/skills/plano-de-testes.md:28`).
- Toda afirmação com origem e nada inventado; lacuna vai para "Perguntas em aberto" (`docs/skills/checklist-revisao.md:50-52`).
- Preencher `PR:` no card, `in_review`, atribuir ao reviewer (`R2`, `R6`).

## 5. Perguntas em aberto

1. **Hospedagem e ambientes** (`§12.10`, `ck-contexto-do-projeto.md:281`): Kubernetes gerenciado, PaaS ou VM única com compose? Toda a seção 2 depende disso.
2. **Registry fixo**: `ghcr.io/leleocastro/companybrain` está cravado no script (`scripts/deploy-staging.sh:6`); a conta `leleocastro` é a dona e o registry é definitivo? (`docs/arquitetura/operacao-estado-atual.md:154`).
3. **Produção sem aprovação no repositório**: `deploy-prod.yml` dispara em `release published` sem gate de revisores (`deploy-prod.yml:3-10`); a proteção do environment será só no GitHub, fora do código? (`docs/arquitetura/operacao-estado-atual.md:152`).
4. **`graph` e `indexer`** viram serviços ou saem? Têm Dockerfile e workflow, mas `§5` não os cita (`docs/arquitetura/operacao-estado-atual.md:153`).
5. **CI por serviço com build**: `.github/pr-body-build.md` descreve um job de build que os workflows atuais não têm; qual é o alvo? (`docs/arquitetura/operacao-estado-atual.md:151`).
6. **Segredos de terceiros** (GitHub App, LLM, Stripe): quem provisiona e em qual cofre? Nada no repositório além de `GITHUB_*` lidos por env (`docs/arquitetura/operacao-estado-atual.md:156`).
7. **Instalação e callback do App**: rota, parâmetro de retorno e vínculo `installation_id` ↔ tenant não estão definidos (`§12.3`; `docs/arquitetura/operacao-estado-atual.md:158`).
8. **Divergência de seção**: o card e o doc de operação citam `§10` para webhooks, mas `§10` é "referência do artigo" (`ck-contexto-do-projeto.md:196`) e o HMAC está lá como descrição do sistema original (`:212`). O alvo do CK é o mesmo? (`docs/arquitetura/operacao-estado-atual.md:139`).
9. **Números de linha da fonte**: `operacao-estado-atual.md` foi escrito sobre o commit `4e37951` (`:3`); a `main` avançou. As linhas de código citadas aqui foram reconferidas nesta skill, mas as citações ao próprio documento podem deslocar quando ele for editado.
