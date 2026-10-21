# Checklist de revisão de PR — CompanyKnowledge

Checklist do reviewer para PRs do CompanyBrain. Cada item cita a origem: `caminho:linha` para o que existe no repositório, `§N` para o `ck-contexto-do-projeto.md`, `R N` para as regras de fluxo do projeto. O repositório manda: se o código diverge do contexto, registre a divergência, não a "conserte" na revisão (`§0`).

## 1. Antes de ler o diff

- [ ] O card está `in_review` e atribuído a mim; o PR está no campo `PR:` do card.
- [ ] Li os critérios de aceite do card e consigo apontar o item de código/doc que atende cada um.
- [ ] O PR tem uma responsabilidade só e até ~200 linhas (`R9`). Acima disso, devolver para quebrar (conta como devolução).
- [ ] O título/vínculo do PR segue o tipo do card:
  - código: a KEY do card **está** no título (`CK-<n>: ...`);
  - `docs`: a KEY **não** aparece no título, no corpo (`Closes`/`Fixes`/`Resolves`) nem na branch (`docs/<assunto>`).
- [ ] O diff não traz mudança fora do escopo do card (ex.: card `docs` que altera código).

## 2. Código

### Convenções e formatação

- [ ] Python: `black` e `isort` com `profile = "black"` e 88 colunas (`pyproject.toml:1-16`); `flake8` com 88 e `E203,W503` ignorados (`pyproject.toml:18-22`).
- [ ] O pre-commit passa: `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-json`, `check-merge-conflict` (`.pre-commit-config.yaml:2-10`).
- [ ] JS/TS/JSON/CSS/Markdown: `prettier` (`.pre-commit-config.yaml:27-31`); `.js/.jsx/.ts/.tsx`: `eslint` (`.pre-commit-config.yaml:32-39`; config em `web/.eslintrc.json`).
- [ ] Não introduziu linter/formatter novo sem card: o CI já fixa `ruff check .` e `ruff format --check .` por serviço (`.github/workflows/service-api.yml:29-30`).

### Testes e CI

- [ ] Mudança de comportamento vem com teste que falha antes e passa depois.
- [ ] Os testes rodam onde o CI espera: `pytest` com `asyncio_mode = "auto"` e `testpaths` de `pyproject.toml:24-27`.
- [ ] O CI do serviço tocado roda lint e teste (`.github/workflows/service-{api,ingestao,graph,indexer,web}.yml`); o workflow geral roda `tests/` com `GDRIVE_TEST_MODE=mock` (`.github/workflows/ci.yml:33`).
- [ ] Nenhum teste depende de rede, credencial real ou ordem de execução.

### Contratos e fronteiras

- [ ] O contrato de conector foi preservado: `Document` e `BaseConnector` (`ingestao/connectors/base.py:10-48`); um conector novo herda de `BaseConnector`, não duplica o pipeline.
- [ ] A API existente mantém os modelos Pydantic `Node`, `Edge`, `PaginatedNodes`, `PaginatedEdges`, `NodeDetail` (`api/mock_graph/main.py:19-47`) — mudança de campo é mudança de contrato e precisa de aval do tech-lead.
- [ ] A fronteira `web → api` continua em `/api/*` via proxy do nginx (`docker/web.nginx.conf`); nada de URL absoluta ou CORS aberto (`api/mock_graph/main.py:11-16`).
- [ ] O `Document`/`SourceDocument` normalizado é o ponto de saída da ingestão (`ingestao/models.py:9`); não inventar transporte (fila/HTTP) sem card da Fase 2.

### Segurança, isolamento e segredos

- [ ] Todo dado lido/gravado carrega `tenant_id`; nenhuma query, coleção ou path cruza tenant (`§7`; alvo em `§5` Backend/Armazenamento).
- [ ] Logs novos incluem `tenant_id` e não logam conteúdo de documento, e-mail ou token (`§5` Observabilidade).
- [ ] Nenhum segredo no diff: token, senha, chave privada, `.env` (`R14`; `.gitignore` cobre `.env`; pre-commit tem `detect-private-key` em `.pre-commit-config.yaml:11`).
- [ ] Segredos vêm de ambiente, como o conector GitHub já faz (`ingestao/github_connector/auth.py:40-61`), e credencial não aparece em `repr` (`auth.py:31`).
- [ ] Input de webhook é verificado por HMAC antes de processar (`ingestao/github_connector/webhooks.py`); PII passa por `redact_pii` quando o dado sai da ingestão (`ingestao/pii.py:14`).
- [ ] Exclusão/exportação de workspace e retenção seguem `§7` quando o PR tocar dados persistidos.

## 3. Documentação

- [ ] Toda afirmação do doc tem origem verificável (`caminho:linha` ou `§N`) e nada foi inventado (`R16`).
- [ ] Divergência entre código e contexto está registrada, não resolvida dentro do PR (`§0`).
- [ ] O que não se sabe está em "Perguntas em aberto"; não há suposição apresentada como fato.
- [ ] Doc curto e escaneável (títulos e listas); skill com até ~100 linhas.
- [ ] Arquivo no lugar decidido pelo tech-lead: `docs/` na raiz, uma pasta por tipo (`docs/arquitetura/`, `docs/skills/`, `docs/produto/`).
- [ ] Cobre o checklist da área do papel que o produziu (backend, frontend, operação, QA, revisão).

## 4. Como registrar a reprovação

- [ ] Feedback vai **no PR do GitHub** (`gh pr review`), nunca no card (`R6`).
- [ ] Cada apontamento diz o arquivo/linha, o que está errado, a regra violada (com origem) e a ação esperada. Sem "melhorar isso".
- [ ] O card recebe só o handoff: label `retorno-1` (ou `retorno-2`), status `in_progress` e atribuição ao `Dev:` do card (ou autor do PR).
- [ ] Duas devoluções no mesmo card já é o limite; na terceira, `refinement` + tech-lead (`R7`).
- [ ] Aprovação de código: status `qa` + QA **antes** do merge. Aprovação de `docs`: merge e `acceptance` + po.

## 5. Fora do papel do reviewer

- Escopo, preço, contrato de API, segurança/LGPD e arquitetura: decisão do tech-lead ou do humano, não do reviewer (`R10`, `R15`).
- Escrever o código da correção: devolver com o apontamento e o dev corrige (`R6`).
- Revisar card de outro agente ou "ajudar" sem atribuição (`R3`).

## Perguntas em aberto

- O card cita `§10` do contexto; o arquivo salta de `§9` para `§11` (`ck-contexto-do-projeto.md:177`, `:248`). Qual seção deveria ser lida pelo reviewer?
- `docs/skills/` ainda não existe em `main`; a decisão da pasta está em `docs/arquitetura/arquitetura-ck.md` §5.1 (PR #15, aberto). Se o PR #15 mudar, esta skill muda de lugar.
- `.github/workflows/service-web.yml` roda `ruff`/`pytest` em `web/`, que é Node e não tem `requirements-dev.txt` — o CI do frontend não valida o frontend. Divergência registrada, não corrigida aqui (card `docs`).
- `docs/` não está nos `paths` de nenhum workflow de serviço; não há CI de Markdown além do prettier do pre-commit. Confirmar se isso basta.
