# CompanyBrain Web

Interface web single-page com visualização de grafo de conhecimento estilo Obsidian.

## Stack

- React 18 + Vite 6 + TypeScript
- d3-force (simulação força-direcionada)
- Tailwind CSS 3 (dark mode Catppuccin Mocha)

## Desenvolvimento

```bash
npm install
npm run dev
```

Acessar http://localhost:5173

## Build

```bash
npm run build
npm run preview
```

## API

Por padrão usa dados mock em `src/data/mock-graph.ts`. Para conectar à API real em http://localhost:8000, substituir o fetch em `src/data/mock-graph.ts`.

## Estrutura

```
src/
  components/
    GraphView.tsx    — Grafo força-direcionada com drag, zoom, pan
    SearchBar.tsx    — Busca textual com autocomplete
    SidePanel.tsx    — Painel lateral com detalhes do nó
  data/
    mock-graph.ts    — Dados mock para desenvolvimento offline
  types.ts           — Tipos compartilhados (GraphNode, GraphEdge)
  App.tsx            — Layout principal
  main.tsx           — Entry point
```
