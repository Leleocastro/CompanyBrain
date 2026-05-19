## Descrição

Criação de workflows de CI específicos por serviço com lint, teste e build, conforme [LTA-25](mention://issue/86f55748-2fc1-4ee6-be5e-ee59fa686302).

### O que foi adicionado

- **`.github/workflows/ingestao-ci.yml`** — CI para serviço de ingestão (lint + test)
- **`.github/workflows/indexer-ci.yml`** — CI para indexador (lint + test)
- **`.github/workflows/graph-ci.yml`** — CI para grafo (lint + test)
- **`.github/workflows/api-ci.yml`** — CI para API (lint + test)
- **`.github/workflows/web-ci.yml`** — CI para frontend (lint + test + build)
- **`.github/workflows/ci.yml`** — CI geral (pre-commit hooks)
- **`.gitignore`** — atualizado com padrões Python/JS/coverage

### Características

- Cada workflow dispara apenas quando arquivos do respectivo serviço são alterados
- Cache de dependências (pip/npm) para builds mais rápidos
- Relatório de cobertura via Codecov
- Pipeline em etapas: lint → test → build (web)
