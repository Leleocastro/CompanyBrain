# Front-end do CompanyBrain — estado atual e lacunas (Fase 0)

Retrato do que existe em `web/` e do que falta para a wiki e o chat do alvo. Escopo: só documentação; nenhuma dívida abaixo foi corrigida.

**Base de leitura:** `main` em `ee718ce` (o card cita `4e37951`; `git diff 4e37951..ee718ce -- web/` está vazio, então o retrato do front vale para os dois). Fontes: o repositório CompanyBrain e `ck-contexto-do-projeto.md` (`§N`). O que não está em nenhum dos dois vai para a seção 5.

## 1. Como o front funciona hoje

### 1.1 Stack e entrypoint

- SPA React 18 + Vite 6 + TypeScript, grafo com `d3-force`, Tailwind CSS 3 em dark mode Catppuccin Mocha (`web/README.md:7-9`; `web/package.json:14-32`).
- Sem router, sem biblioteca de estado global e sem cliente HTTP: o app é uma tela só (`web/src/App.tsx:21-53`).
- Entry point: `createRoot` em `#root`, `React.StrictMode`, CSS global com as diretivas do Tailwind (`web/src/main.tsx:6-10`; `web/src/index.css:1-3`).
- HTML fixa `lang="en"` e `class="dark"`; o título da aba é `CompanyBrain` (`web/index.html:2-6`). A interface, porém, está escrita em português (`web/src/components/SearchBar.tsx:52`).

### 1.2 Layout e componentes

- `App` monta um header com busca + título, o grafo ocupando o resto e o painel lateral fixo (`web/src/App.tsx:21-53`).
- `GraphView` desenha um `<svg>` com `d3-force`: simulação criada em `web/src/components/GraphView.tsx:159-171` (link com distância 120 e força proporcional ao peso, carga -300, centro, colisão e `alphaDecay(0.02)`), posições aplicadas por manipulação direta do DOM no `tick` (`:85-133`) em vez de re-render do React.
- Interações do grafo: zoom por roda limitado a 0.1–10 (`web/src/components/GraphView.tsx:189-204`), arrastar nó e pan por Pointer Events (`:206-273`), seleção/desseleção no clique (`:182-187`, `:305-309`), destaque de vizinhos e esmaecimento do resto (`:275-283`).
- `SearchBar` filtra localmente por `label` e `summary` (`web/src/components/SearchBar.tsx:16-22`), navega por setas/Enter/Escape (`:29-41`) e mostra autocomplete com ícone e tipo (`:70-96`). Não há debounce nem chamada de rede.
- `SidePanel` tem largura fixa `w-80`, mostra tipo, resumo, propriedades e conexões do nó selecionado (`web/src/components/SidePanel.tsx:31`, `:48`, `:62-116`); sem nó, exibe um convite para selecionar (`:29-34`).

### 1.3 Estado e dados

- Todo o estado é local: `selectedId` e `searchQuery` em `App` (`web/src/App.tsx:8-9`). O nó selecionado é derivado por `find` (`:13-15`).
- Os dados vêm de uma constante de módulo, não de rede: `import mockData from './data/mock-graph'` (`web/src/App.tsx:5`, `:11`). O arquivo tem 19 nós e 35 arestas fixas, em português, com dados fictícios de pessoas, documentos, repositórios, conversas, entidades e arquivos de código (`web/src/data/mock-graph.ts:4-63`).
- Tipos compartilhados: `NodeType` com seis valores, `GraphNode` (`id`, `label`, `type`, `summary`, `properties`), `GraphEdge` (`source`, `target`, `label`, `weight`) e `GraphData` (`nodes`, `edges`) (`web/src/types.ts:1-21`).
- O README manda "substituir o fetch em `src/data/mock-graph.ts`" para usar a API (`web/README.md:29`), mas não existe `fetch` nesse arquivo — ele exporta a constante e nada mais (`web/src/data/mock-graph.ts:64`). O front nunca chamou a API.

### 1.4 Contrato com a API (`api/mock_graph/main.py`)

O front **não consome** estes endpoints hoje; o contrato existe só no backend.

| Endpoint | O que devolve | Origem |
|---|---|---|
| `GET /api/health` | `{"status": "ok"}` | `api/mock_graph/main.py:88-90` |
| `GET /api/graph/nodes?page&size` | `items`, `total`, `page`, `size`; ~20 nós em memória | `api/mock_graph/main.py:92-96` |
| `GET /api/graph/edges?page&size` | idem, ~30 arestas | `api/mock_graph/main.py:98-102` |
| `GET /api/graph/search?q&page&size` | busca por `label`, `type` e `properties.title` | `api/mock_graph/main.py:104-110` |
| `GET /api/graph/node/{id}` | `node` + `neighbors`, 404 se não existir | `api/mock_graph/main.py:112-127` |

Divergências entre o contrato do backend e os tipos do front (registradas, não corrigidas):

- **Nó:** o backend não tem `summary`; o texto fica em `properties.summary`/`properties.title` (`api/mock_graph/main.py:19-24`, `:64`). O front tipa `summary` no topo e o usa na busca e no painel (`web/src/types.ts:3-9`; `web/src/components/GraphView.tsx:292`).
- **Aresta:** o backend usa `type` (`api/mock_graph/main.py:26-30`); o front usa `label` (`web/src/types.ts:11-16`) e o renderiza como rótulo (`web/src/components/GraphView.tsx:330-338`).
- **Paginação:** o backend devolve envelope `items/total/page/size` (`api/mock_graph/main.py:32-42`); `GraphData` espera arrays planos (`web/src/types.ts:18-21`).
- **CORS:** liberado só para `http://localhost:5173` (`api/mock_graph/main.py:11-14`), coerente com o Vite local (`web/vite.config.ts:6-9`).
- **Proxy do container:** o nginx serve a SPA e manda `/api/` para `http://api:8000/` — com a barra final no `proxy_pass`, o prefixo `/api/` é removido (`docker/web.nginx.conf:7-14`), mas as rotas do backend incluem `/api` (`api/mock_graph/main.py:92`). Em produção, `/api/graph/nodes` chegaria como `/graph/nodes`.

## 2. Rodar, buildar e testar

### 2.1 Local

```bash
cd web
npm install
npm run dev        # http://localhost:5173, host exposto na rede
```

Referências: `web/README.md:13-18`, `web/vite.config.ts:6-9`. Não há `npm test`; os scripts existentes são `dev`, `build`, `preview`, `lint`, `format`, `format:fix` (`web/package.json:6-13`).

### 2.2 Build e container

- `npm run build` roda `tsc -b && vite build`; `npm run preview` serve o resultado (`web/package.json:8-9`; `web/README.md:22-25`).
- `npm run lint` é apenas `tsc --noEmit` e `npm run format` é `prettier --check .` (`web/package.json:10-12`). Nenhum script invoca o ESLint, embora `.eslintrc.json` exista (`web/.eslintrc.json:1-17`).
- Imagem: build em `node:20-alpine` com `npm ci` e `npm run build`, servida por `nginx:alpine` na porta 80 (`docker/web.Dockerfile:1-12`). O nginx faz fallback de SPA para `index.html` (`docker/web.nginx.conf:7-9`).
- Deploy: staging e produção constroem `docker/<service>.Dockerfile` e fazem push para `ghcr.io/leleocastro/companybrain` (`scripts/deploy-staging.sh:11-19`; `.github/workflows/deploy-staging.yml:49-57`).

### 2.3 O que o CI valida hoje

- `.github/workflows/service-web.yml` dispara em push/PR que mexam em `web/**` (`.github/workflows/service-web.yml:3-12`), mas roda **Python**: `setup-python` 3.11, `pip install -r requirements-dev.txt`, `ruff check .`, `ruff format --check .` e, no job de teste, `pytest --cov` em Python 3.10/3.11/3.12 (`:19-50`).
- Em `web/` não existe `requirements-dev.txt`, nenhum `.py` e nenhum teste (conteúdo de `web/` listado em `web/README.md:33-44`; `web/package.json:6-13`). Ou seja: o CI não valida o front (nem `tsc`, nem `vite build`, nem Prettier) e tende a falhar no próprio `pip install`.
- O workflow parece copiado do serviço `api`, que tem `requirements-dev.txt` e testes (`api/requirements-dev.txt:1`; `api/mock_graph/test_main.py:12-40`).

## 3. Convenções e dívidas

### 3.1 Convenções observadas

- Componentes de função com _default export_, hooks (`useState`, `useMemo`, `useCallback`, `useRef`, `useEffect`) e props tipadas por interface local (`web/src/App.tsx:1-19`; `web/src/components/GraphView.tsx:9-16`).
- TypeScript estrito: `strict`, `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch` (`web/tsconfig.json:15-19`), `jsx: react-jsx` e `moduleResolution: bundler` (`:9-14`).
- Prettier: aspas simples, ponto e vírgula, `trailingComma: es5`, 2 espaços, 88 colunas (`web/.prettierrc:1-8`).
- Tailwind com `darkMode: 'class'` e paleta própria (`surface`, `border`, `text`, `accent`) em `web/tailwind.config.js:2-30`; cores também aparecem duplicadas em constantes nos componentes (`web/src/components/GraphView.tsx:35-51`; `web/src/components/SidePanel.tsx:10-26`).
- Textos de UI em pt-BR; nomes de código e comentários em inglês/português misturados, sem padrão declarado.

### 3.2 Dívidas e divergências (não corrigidas)

1. Front 100% mockado; a "conexão com a API" descrita no README não existe (`web/README.md:29` × `web/src/App.tsx:5-11`).
2. Contrato de nó/aresta/paginação incompatível entre `web/src/types.ts:3-21` e `api/mock_graph/main.py:19-42`.
3. Proxy do nginx remove `/api/` e quebra as rotas do backend (`docker/web.nginx.conf:11-12` × `api/mock_graph/main.py:92`).
4. CI do web valida Python inexistente em `web/` (`.github/workflows/service-web.yml:19-50`).
5. ESLint configurado mas fora dos scripts; e o `.eslintrc.json` não usa parser de TypeScript (`web/.eslintrc.json:1-17`; `web/package.json:6-13`).
6. Layout não responsivo: painel fixo de 320px e `w-screen h-screen` (`web/src/components/SidePanel.tsx:31`, `:48`; `web/src/App.tsx:22`).
7. Ícones e cores de tipo repetidos em dois componentes (`web/src/components/GraphView.tsx:35-51`; `web/src/components/SidePanel.tsx:10-26`), sem fonte única.

## 4. O que falta para wiki e chat do alvo

### 4.1 Wiki por tenant (`§5` Wiki, `§6` Consulta)

O alvo pede build estático **por tenant**, servido em subdomínio próprio, com busca full-text + semântica, graph view dos documentos, versionamento com histórico e citação de origem em cada página (`§5:104-105`). A consulta inclui buscar na wiki, navegar pelo grafo e ver o histórico de versões (`§6:139-140`).

O que existe hoje: apenas o grafo em memória, sem páginas de documento, sem Markdown, sem busca na wiki e sem histórico. O que falta:

- Rotas/URLs de wiki (a SPA atual não tem router: `web/src/App.tsx:21-53`).
- Renderização de Markdown e layout de página com metadados e citações.
- Busca full-text + semântica (hoje a busca é `includes` local: `web/src/components/SearchBar.tsx:16-22`).
- Histórico/versionamento e "quando mudou e por quê" (`§5:105`).
- Contexto de tenant no front; não há login, sessão nem `tenant_id` (`§5:78-79`).
- Fonte de dados real: build estático por tenant em object storage (`§5:102`, `§5:105`) ou API — o repo não tem gerador de wiki nem endpoint de páginas.

### 4.2 Chat nas duas superfícies (`§5` Chat, `§6` Consulta)

O alvo é um motor RAG único com citações, exposto em duas superfícies: embutido na wiki (pesquisa contextual) e standalone estilo ChatGPT/OpenWebUI, com histórico por usuário e joinha/negativo em cada resposta (`§5:107-110`). A resposta deve trazer citações clicáveis (`§6:140`).

O que existe hoje: nada de chat — nenhum componente, nenhuma chamada de rede, nenhum streaming (`web/src/App.tsx:21-53`; busca por "chat" em `web/src/` não retorna resultados). O que falta:

- Componente de chat e, para a superfície standalone, uma rota/tela própria.
- Cliente HTTP/streaming e contrato de pergunta-resposta com citações (não definido no repo nem em `§5`/`§6`).
- Histórico de conversas por usuário e feedback por resposta (`§5:110`).
- Embed do chat dentro da página da wiki, com contexto da página (`§5:109`).
- Autenticação/sessão para identificar o usuário do histórico (`§5:79`, `§5:110`).

### 4.3 Base transversal que ambas exigem

- Camada de API no front (hoje inexistente; ver 3.2 item 1) e tratamento de erro/carregamento.
- Sessão e tenant (`§5:78-79`); sem isso não há wiki nem histórico isolados por cliente.
- Citações como componente reutilizável (wiki `§5:105`, chat `§5:108`, consulta `§6:140`).
- i18n: `§9:192` exclui múltiplos idiomas do v1, mas não define qual idioma único (`§12:283`); a UI atual está em pt-BR (`web/src/components/SearchBar.tsx:52`).
- Painel do cliente e onboarding do GitHub App (`§5:120-121`, `§6:133-134`) não são escopo deste documento, mas compartilham a mesma base de sessão/tenant.

## 5. Perguntas em aberto

1. **Contrato da API de wiki e de chat.** `§5`/`§6` descrevem comportamento, não endpoints; o repo só tem `/api/graph/*` (`api/mock_graph/main.py:88-125`). Quem define os contratos que o front vai consumir? (Pelo fluxo do time, seria o tech-lead; o card manda devolver endpoint faltante a ele.)
2. **Como o front recebe o tenant?** `§5:104-105` fala em subdomínio por cliente e `§5:78-79` em `tenant_id` por request, mas não diz se o front resolve tenant por host, por sessão ou por ambos.
3. **Wiki é build estático consumido direto ou há API de páginas?** `§5:102` e `§5:105` dizem build estático em S3 por tenant; o repo não tem gerador nem pipeline de build de wiki.
4. **Como o chat é embutido na wiki?** `§5:109` diz "embutida na wiki", sem definir componente nativo, iframe ou widget; e como o chat recebe o contexto da página.
5. **`api/mock_graph` é o contrato de referência?** `docs/produto/visao-do-produto.md:157` já questiona o entrypoint do serviço (`api.main` × `api.mock_graph.main`). A resposta muda o formato de nó/aresta/paginação a adotar (3.2 item 2).
6. **Qual lado corrigir no proxy?** `docker/web.nginx.conf:11-12` remove `/api/`; o backend espera `/api/...` (`api/mock_graph/main.py:92`). Não está definido se o prefixo fica no nginx ou nas rotas.
7. **O CI do `web` deve validar o front?** Hoje roda Python sem arquivos Python em `web/` (`.github/workflows/service-web.yml:19-50`). Trocar para `npm ci` + `npm run lint` + `npm run build` é decisão de infra/tech-lead.
8. **Histórico de versões da wiki:** `§5:105` cita "quando mudou e por quê", mas não define modelo de versão nem UI de diff.
9. **Feedback (joinha/negativo):** `§5:110` pede os botões, mas não define para onde vai o feedback nem se o front lê esse estado.
10. **Documento de arquitetura da Fase 0 (`docs/arquitetura/arquitetura-ck.md`, PR #15) não está em `main`**; este documento usou o card, o contexto e `docs/produto/visao-do-produto.md`. Se o PR #15 definir pasta/contratos diferentes, este documento precisa de ajuste.
