# Skill do dev-backend — implementar e testar um card

Procedimento do dev-backend para levar um card de backend de `todo` a `in_review`: branch própria, código testado, PR com a KEY no título. Cada afirmação cita a origem — `caminho:linha` do CompanyBrain ou `§N` do `ck-contexto-do-projeto.md`. O repositório manda: o código é a base, o contexto é o alvo (`§0`).

## 1. Antes de codar

- Confirme o card atribuído a você e leia o corpo inteiro, inclusive `Abordagem técnica:` e `Critérios de aceite:` (`R2`, `R3`).
- Leia só as seções do contexto listadas em `Contexto:` no card, não o arquivo inteiro (`AGENTS.md`).
- Crie uma branch própria a partir da `main`; nunca commite na `main`.
- Localize o módulo antes de escrever: `ingestao/` (conectores, normalização, PII), `api/mock_graph/` (único `FastAPI` do repo, `api/mock_graph/main.py:7`). `graph/`, `indexer/` e `web/` são placeholders (`graph/README.md`, `indexer/README.md`, `graph/.placeholder`).
- Preserve o que existe: `Document`/`BaseConnector` (`ingestao/connectors/base.py:10`, `:25`), registry (`ingestao/connectors/__init__.py:11`) e os modelos Pydantic da API (`api/mock_graph/main.py:19-47`). Campo de contrato só muda com aval do tech-lead (`docs/skills/checklist-revisao.md`).
- Card fora do backend (front, infra, domínio): `refinement` + tech-lead, sem comentário (`R10`).

## 2. Rodar e testar (da raiz do repo)

Pré-requisito: Python 3.11 nos containers (`docker/*.Dockerfile:1`); o CI testa a matriz 3.10–3.12 (`.github/workflows/service-ingestao.yml:37`).

```bash
pip install -r requirements.txt
pip install "pytest>=8.2,<9" pytest-asyncio==0.25.0 pytest-httpx==0.35.0 \
  pytest-mock httpx==0.28.1 PyJWT==2.10.1 "slack_sdk>=3.27,<4"

python -m pytest -q ingestao api                  # 98 passed (2026-10-21)
GDRIVE_TEST_MODE=mock python -m pytest -q tests/  # 24 passed (Drive)
```

- Não instale `ingestao/requirements-dev.txt` nem `api|graph|indexer/requirements-dev.txt`: `pytest==8.0.0` não resolve com `pytest-asyncio==0.25.0`, e os três últimos apontam para o primeiro (`backend-estado-atual.md:105`, `:107`).
- **`ingestao`**: `python -m pytest -q ingestao/tests ingestao/github_connector/tests ingestao/connectors/gmail/tests`; smoke do Gmail: `python ingestao/connectors/gmail/smoke_test.py` (5 PASS, `backend-estado-atual.md:92`); CLIs: `python -m ingestao.github_connector.main --help` (`backend-estado-atual.md:96`).
- **`api`**: da raiz, `python -m pytest -q api/mock_graph/test_main.py` — rodar de dentro de `api/` dá `ModuleNotFoundError`, porque `api/` não tem `__init__.py` (`backend-estado-atual.md:108`). Local: `uvicorn api.mock_graph.main:app --reload`; não há comando documentado no repo (`backend-estado-atual.md:97`).
- **`graph` e `indexer`**: não há código nem teste, só `.placeholder`; o `requirements-dev.txt` redireciona para a ingestão (`graph/requirements-dev.txt:1`). Não há o que rodar.
- **`web`** (Node, não Python): `cd web && npm install && npm run dev` (http://localhost:5173), `npm run build`, `npm run lint`, `npm run format` (`web/README.md`; `web/package.json:6-12`). Sem teste automatizado.
- Suíte de Drive fora do pytest: `GDRIVE_TEST_MODE=mock python run_gdrive_tests.py` (`.github/workflows/ci.yml:36`).

## 3. Convenções

- Python 3.11; `black` e `isort` (`profile = "black"`) em 88 colunas, `flake8` 88 com `E203,W503` ignorados (`pyproject.toml:1-22`).
- Contratos em `dataclass`; HTTP com `httpx.AsyncClient`; `from __future__ import annotations` nos módulos que já usam (`backend-estado-atual.md:115`).
- Configuração por variável de ambiente (`ingestao/github_connector/auth.py:39-62`); segredo com `repr=False` e nunca em log ou diff (`auth.py:28`; `R14`).
- Teste junto do código (`ingestao/github_connector/tests/`, `ingestao/connectors/gmail/tests/`) e também na raiz (`tests/`); `python_files = ["test_*.py", "*_test.py"]` (`pyproject.toml:27`).
- Sem camadas, migrations ou injeção de dependência: não invente estrutura nova para card pequeno (`backend-estado-atual.md:119`).
- O CI usa `ruff check .` e `ruff format --check .` por serviço, sem config de ruff no repo; localmente valem `black`/`isort`/`flake8` do pre-commit (`.pre-commit-config.yaml:12-22`; `backend-estado-atual.md:118`).
- **Isolamento por `tenant_id` é alvo, não fato**: não existe `tenant_id` em nenhum `.py` do repo (`backend-estado-atual.md:70`). Quando o código existir, toda leitura/gravação, coleção, path e log carrega `tenant_id` e nada cruza tenant (`§7`; `§5` Backend/Observabilidade). Não introduza `tenant_id` cosmético sem card.

## 4. Antes do PR

- [ ] Teste escrito no caminho que o CI espera (`pyproject.toml:24-27`); mudança de comportamento vem com teste que falha antes e passa depois.
- [ ] Rode a suíte do serviço tocado e cole a saída (pass/fail) no PR; teste não depende de rede, credencial real ou ordem.
- [ ] Se tocar dado pessoal na ingestão, garanta a redação antes de sair (`§7`); hoje só o Drive redige (`ingestao/connectors/google_drive/normalizer.py:23`) — nos outros, é exigência a implementar, não comportamento existente.
- [ ] Uma responsabilidade por PR, até ~200 linhas (`R9`); branch própria e a KEY do card no título (`CK-<n>: ...`).
- [ ] Preencha `PR:` e `Premissas:` no card e faça o handoff `in_review` + reviewer (`R2`, `R6`).
- [ ] Card `docs`: branch `docs/<assunto>`, título sem a KEY e sem `Closes`/`Fixes`/`Resolves` com a KEY; vínculo só pelo link no campo `PR:`.

## Perguntas em aberto

- **Entrypoint da Fase 1**: corrigir `docker/api.Dockerfile:12` (`api.main:app`, que não existe) ou evoluir `api.mock_graph`? (`backend-estado-atual.md:150`).
- **Lint**: o CI exige `ruff` sem configuração, o local usa `black`/`isort`/`flake8` (`backend-estado-atual.md:118`). Qual manda quando o `ruff` reprova um arquivo que o `black` aceita?
- **Deps de teste**: `ingestao/requirements-dev.txt` segue quebrado (`backend-estado-atual.md:105`). Consertar é card próprio? Até lá, use o comando da seção 2.
- **Multi-tenant**: onde nasce o backend com `tenant_id` e onde rodam os testes de isolamento, se não há staging (`docs/skills/plano-de-testes.md` §3; `§12.10`)?
- **Repositório**: card cita CK-21 (greenfield x CompanyBrain) e CK-20 (perguntas da Fase 0); até decisão de João Pedro Rocha, vale o CompanyBrain.
