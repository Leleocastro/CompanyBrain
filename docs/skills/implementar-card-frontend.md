# Implementar e testar um card no front — dev-frontend

Procedimento do dev-frontend em todo card que toca `web/`. Cada afirmação cita `caminho:linha` do CompanyBrain ou `§N` do `ck-contexto-do-projeto.md`; o que não está em nenhum dos dois vai para "Perguntas em aberto". O repositório manda: se o código divergir do alvo, registre, não conserte de passagem (`§0`).

## 1. Antes de codar

- Card em `todo` atribuído a mim → `in_progress --no-start`; branch própria, KEY do card no título do PR.
- Ler o card inteiro e depois `docs/arquitetura/frontend-estado-atual.md` §2 (rodar/buildar/testar), §3 (convenções) e §4 (lacunas de wiki/chat).
- Localizar a superfície antes de editar:
  - Grafo, busca e painel: `App` monta header + `GraphView` + `SidePanel` (`web/src/App.tsx:21-54`); componentes em `web/src/components/`.
  - Tipos compartilhados de nó/aresta/grafo: `web/src/types.ts:1-21`.
  - Entry point: `createRoot` em `#root` com `React.StrictMode` (`web/src/main.tsx:6-10`).
- Dados hoje vêm de constante de módulo, não de rede (`web/src/App.tsx:5`; `web/src/data/mock-graph.ts:64`); não existe `fetch` no front (`frontend-estado-atual.md:29`).
- Superfícies alvo ainda não existem: wiki por tenant (`§5:104-105`) e chat em duas superfícies (`§5:107-110`) não têm rota, componente nem cliente HTTP (`frontend-estado-atual.md:103-122`). Não há router: o app é tela única (`web/src/App.tsx:21-54`).
- Contrato de API não se inventa no front: endpoint faltante volta ao tech-lead (`R10`). O único contrato no repo é `/api/graph/*` (`api/mock_graph/main.py:88-127`) e o front não o consome (`frontend-estado-atual.md:33`).

## 2. Rodar, buildar e testar

```bash
cd web
npm install
npm run dev          # http://localhost:5173 (web/vite.config.ts:6-9)
npm run lint         # tsc --noEmit (web/package.json:10)
npm run format       # prettier --check . (web/package.json:11)
npm run build        # tsc -b && vite build (web/package.json:8)
npm run preview      # serve o build (web/package.json:9)
```

- Não existe `npm test` nem teste em `web/` (`web/package.json:6-13`; `web/README.md:33-44`). Evidência possível hoje: `lint` + `build` verdes e o caminho manual no navegador — descreva tela, ação e resultado em `Dev:`.
- Container: `npm ci` + `npm run build` em `node:20-alpine`, servido por `nginx:alpine` (`docker/web.Dockerfile:1-12`).
- O CI **não** valida o front: `.github/workflows/service-web.yml:19-50` instala `requirements-dev.txt`, roda `ruff` e `pytest` num diretório Node. Rode os comandos acima na mão e diga no PR que o CI não cobre o front.

## 3. Convenções

- Componente de função, _default export_, props em interface local; TS estrito com `noUnusedLocals`/`noUnusedParameters` (`web/src/App.tsx:1-19`; `web/tsconfig.json:15-19`).
- Prettier: aspas simples, ponto e vírgula, `trailingComma: es5`, 2 espaços, 88 colunas (`web/.prettierrc:1-7`). Rode `npm run format:fix` antes do commit.
- Pre-commit aplica Prettier em `js/jsx/ts/tsx/json/css/markdown` e ESLint em `.[jt]sx?` (`.pre-commit-config.yaml:27-39`).
- ESLint existe mas não está nos scripts e o `.eslintrc.json` não tem parser de TypeScript (`web/.eslintrc.json:1-17`; `web/package.json:6-13`): `npm run lint` é só `tsc`.
- Tailwind em `darkMode: 'class'` com paleta `surface`/`border`/`text`/`accent` (`web/tailwind.config.js:2-30`); UI em pt-BR (`web/src/components/SearchBar.tsx:52`) com `lang="en"` no HTML (`web/index.html:2`).
- Fronteira `web → api`: só `/api/*` relativo, via proxy do nginx (`docker/web.nginx.conf:11-15`); nada de URL absoluta. O CORS do mock libera apenas `http://localhost:5173` (`api/mock_graph/main.py:10-16`).
- Divergência a não corrigir de passagem: `proxy_pass http://api:8000/` com barra final remove `/api/` (`docker/web.nginx.conf:12`), mas as rotas do backend já incluem `/api` (`api/mock_graph/main.py:88-112`) — em produção `/api/graph/nodes` chega como `/graph/nodes`.

## 4. Antes do PR

- Rodar `npm run lint`, `npm run format` e `npm run build` em `web/` e colar a saída (ou o final dela) em `Dev:` no card.
- Escrever no PR a superfície tocada, o que foi verificado manualmente e as limitações (sem teste automatizado, CI do front quebrado).
- Card de código: KEY no título do PR; link só no campo `PR:` do card; sem comentário e sem menção (`R1`, `R4`).
- Decisão pequena sua → `Premissas:`; lacuna ou divergência com o documento de origem → "Perguntas em aberto" do documento, sem resolver no PR (`R16`).

## Perguntas em aberto

1. **Quem valida o front no CI?** O workflow de `web` roda Python (`frontend-estado-atual.md:140`). Trocar por `npm ci` + `lint` + `build` é decisão de infra/tech-lead; este card é `docs` e não corrige.
2. **Onde se corrige a fronteira `/api/`?** nginx ou rotas do backend (`frontend-estado-atual.md:139`). Até a decisão, o proxy do container quebra as rotas.
3. **Qual contrato de wiki e de chat o front consome?** `§5`/`§6` descrevem comportamento, não endpoints (`frontend-estado-atual.md:134`). Sem contrato, não há cliente HTTP a implementar.
4. **Todo card de front exige teste automatizado?** Não há framework de teste em `web/` (`web/package.json:6-13`). Se sim, entra um card de infra para escolher e ligar o runner.
5. **ESLint fica fora dos scripts?** Config sem parser de TS e fora do `npm run lint` (`frontend-estado-atual.md:93`). Arrumar é card próprio, não item de todo card.
6. **Vale CompanyBrain até quando?** CK-21 (repositório novo greenfield x CompanyBrain) e CK-20 (perguntas da Fase 0) podem mover esta skill de repositório. Até a decisão de João Pedro Rocha, vale o CompanyBrain e a pasta `docs/skills/` (`docs/arquitetura/arquitetura-ck.md:122-130`).
