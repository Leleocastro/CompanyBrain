# Plano de testes do CK (Fase 1)

Skill do qa. Diz o que já dá para testar hoje, como rodar, os cenários alvo da Fase 1 e o que depende de ambiente que não existe. Base: `main` em `ee718ce` (inclui `4e37951`). Origem de cada item: seção do `ck-contexto-do-projeto.md` (`§N`) ou `caminho:linha`. O repositório manda para "como é hoje"; cenário sem código é alvo, não fato.

## 1. O que dá para testar hoje

Tudo local e em mock, sem credencial real. Num venv limpo:

```
python -m pip install -r requirements.txt -r api/mock_graph/requirements.txt \
  "pytest>=8.2" pytest-asyncio pytest-httpx pytest-mock slack_sdk PyJWT
```

Não usar `-r ingestao/requirements-dev.txt`: os pins dele não resolvem entre si (ver 4).

| Suíte | Cobre | Como rodar | Observação |
|---|---|---|---|
| Google Drive (24) | connector mock, auth, list/download/ingest, normalizer, PII (`tests/test_google_drive_client.py:9`, `tests/test_google_drive_normalizer.py:13`) | `GDRIVE_TEST_MODE=mock python -m pytest tests -v` | em CI: `.github/workflows/ci.yml:33` |
| Google Drive (runner) | mesmos casos sem pytest (`run_gdrive_tests.py:1`) | `GDRIVE_TEST_MODE=mock python run_gdrive_tests.py` | em CI: `.github/workflows/ci.yml:36` |
| Slack (14) | auth, canais, threads, normalização (`ingestao/tests/test_auth.py:5`, `test_channels.py:4`, `test_threads.py:4`, `test_normalize.py:4`) | `python -m pytest ingestao/tests -v` | precisa `slack_sdk` + `pytest-mock` |
| GitHub (45) | auth PAT/App/OAuth (`test_auth.py:10`), client REST (`test_client.py:21`), ingestor com `since` (`test_ingestor.py:18`), normalizer (`test_normalizer.py:18`), webhook HMAC (`test_webhooks.py:8`) | `python -m pytest ingestao/github_connector/tests -v` | precisa `pytest-httpx` |
| Gmail (29) | auth mock, client, config, parser (`ingestao/connectors/gmail/tests/test_auth.py:5`, `test_client.py:13`) | `python -m pytest ingestao/connectors/gmail/tests -v` | mock, sem rede |
| Gmail smoke (5) | imports, config, OAuth mock, parser (`ingestao/connectors/gmail/smoke_test.py:126`) | `python ingestao/connectors/gmail/smoke_test.py` | self-contained |
| Mock Graph API (5) | health, paginação, busca, nó+vizinhos (`api/mock_graph/test_main.py:6`) | `python -m pytest api/mock_graph/test_main.py -v` (da raiz) | — |

Verificado em 2026-10-21 com o comando acima (Python 3.14, pytest 9.1.1): 24 + 14 + 45 + 29 + 5 = 117 testes verdes, mais `run_gdrive_tests.py` e o `smoke_test.py` do Gmail (5/5).

Evidência: saída do `pytest` (pass/fail) anexada ao card ou link do run de CI. Hoje **não há código** para `tenant_id`, auth de API key/sessão, pipeline de PR, wiki, chat ou Stripe (`§5`; `grep -rn tenant` em `*.py`/`*.ts`/`*.tsx` = 0 ocorrências).

## 2. Cenários da Fase 1 (alvo)

Formato: Dado / Quando / Então, origem e evidência esperada. "Hoje" indica se já executa.

**2.1 Isolamento multi-tenant — `tenant_id`** (`§5` Backend/Armazenamento, `§7`)
- Dado tenants A e B com dados indexados, quando B consulta a memória, então nada de A aparece (busca textual e vetorial).
- Dado documento criado por A, quando inspecionado em Postgres/Qdrant/storage, então carrega `tenant_id` de A.
- Evidência: resposta com 0 itens de A + log estruturado com `tenant_id` + registro no banco. Hoje: não.

**2.2 Auth — API key e sessão** (`§5` Backend, `§7`)
- Dado tenant A, quando chama endpoint sem key ou com key revogada, então 401.
- Dado key de B, quando acessa recurso de A, então 403/404 e corpo sem dado.
- Dado sessão de usuário de A, quando abre wiki/painel de B, então nega acesso e registra tentativa.
- Evidência: status HTTP + corpo + log de auditoria (hash da key, tenant, rota). Hoje: não.

**2.3 GitHub App e backfill** (`§5` Ingestão, `§6` cadastro/onboarding, `§8` tabela de planos)
- Dado payload com `X-Hub-Signature-256` válido, quando chega o webhook, então aceita e enfileira; inválido, então rejeita (base testada: `ingestao/github_connector/webhooks.py:24`, `test_webhooks.py:8`).
- Dado instalação com PRs fora da janela do plano (Essencial 3 meses, Profissional 12) e PRs de bot/merge/minúsculo, quando o backfill roda, então processa só a janela e registra o motivo do descarte.
- Evidência: log de entrega do webhook + contagem de PRs processados vs. ignorados por motivo. Hoje: só o webhook isolado.

**2.4 Pipeline de PR** (`§5` Pipeline)
- Dado PR mergeado, quando processa, então gera Markdown versionado com modelo barato, cita repositório/PR/arquivo e reindexa o gerado.
- Dado o mesmo PR entregue duas vezes (retry), quando reprocessa, então não duplica versão (idempotência).
- Evidência: artefato/registro gerado + versão/commit + citação de origem na página + log com id do evento. Hoje: não.

**2.5 Wiki** (`§5` Wiki)
- Dado tenant A com build, quando abre o subdomínio de A, então páginas, busca (full-text + semântica), graph view e citações funcionam; o subdomínio de B não abre conteúdo de A.
- Dado página alterada, quando abre o histórico, então mostra quando mudou e por quê.
- Evidência: URL + texto/print da página com citações + diff de versões. Hoje: não (só `web/` com grafo mock).

**2.6 Chat** (`§5` Chat)
- Dado pergunta sobre conteúdo de A, quando responde, então toda afirmação tem citação clicável da fonte (wiki e standalone).
- Dado pergunta cuja resposta só existe em B, quando A pergunta, então não há vazamento e a resposta admite falta de fonte.
- Dado joinha/negativo, quando enviado, então fica registrado por usuário/resposta.
- Evidência: transcrição + links de citação + id do documento citado. Hoje: não.

**2.7 Stripe — base fixa** (`§5` Billing, `§8`; excedente/trava de gasto ficam para a Fase 2, `§9`)
- Dado tenant no Essencial (R$ 249/mês), quando assina, então a base fixa é criada e o portal de cobrança abre.
- Dado webhook do Stripe repetido, quando chega, então não duplica assinatura/cobrança (idempotência).
- Evidência: evento no Stripe test mode + estado da assinatura no CK + invoice. Hoje: não.

## 3. Ambientes

- **Local**: único executável hoje. Criar um venv e instalar as deps da seção 1 (o host não traz `pytest`).
- **CI**: GitHub Actions por serviço (`.github/workflows/service-*.yml`) e `ci.yml` (Google Drive). É onde as suítes da seção 1 rodam de fato, em Python 3.10–3.12 (`.github/workflows/service-ingestao.yml:37`).
- **Staging**: **não existe** no repositório. `scripts/deploy-staging.sh:22` faz `kubectl apply` de um `echo` com `|| true`; não há compose, manifests nem URL. Portanto 2.1–2.7 não têm onde rodar hoje.
- Evidência mínima por cenário: teste automatizado verde + o log/resposta/tela descrito em cada item.

## 4. Divergências observadas (não corrigidas aqui)

- `ingestao/requirements-dev.txt:5` (`pytest==8.0.0`) e `:6` (`pytest-asyncio==0.25.0`, que exige `pytest>=8.2`) não resolvem juntos: `pip install -r ingestao/requirements-dev.txt` termina em `ResolutionImpossible`. Isso atinge os jobs `lint`/`test` de `.github/workflows/service-ingestao.yml:28,45` e, por tabela, `api/requirements-dev.txt:1` (`service-api.yml:28,45`).
- `.github/workflows/service-web.yml:27` fixa `cache-dependency-path: web/requirements*.txt` e `:28` instala `web/requirements-dev.txt`, mas `web/` é React/Vite e não tem esses arquivos.
- O `testpaths` (`pyproject.toml:25`) aponta para `indexer/tests`, `graph/tests` e `api/tests`, que não existem; os testes de `ingestao` e `api` vivem fora desses caminhos.
- `pyproject.toml:25` não inclui `ingestao/connectors/gmail/tests` quando o pytest é disparado da raiz.

## 5. Perguntas em aberto

1. Onde 2.1–2.7 vão rodar? Staging não existe e o material não define ambientes (`§12.10`). Preciso de URL, forma de obter credenciais e o que conta como "staging" no aceite.
2. `docs/arquitetura/arquitetura-ck.md` (PR #15) ainda não está no `main`; a pasta `docs/skills/` veio do card. Confirmar quando o doc entrar.
3. Existem contas/dados de teste (dois tenants, repo GitHub de teste, Stripe test mode) ou devo criar? Envolve credenciais de terceiros.
4. Não há critério de "pronto" por fase (`§12.2` não define). Uso os cenários de 2.x como proxy até o po definir.
