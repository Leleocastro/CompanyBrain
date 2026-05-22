import { useState } from 'react'
import GraphView from './components/GraphView'
import SidePanel from './components/SidePanel'
import SearchBar from './components/SearchBar'
import mockData from './data/mock-graph'

export default function App() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const { nodes, edges } = mockData

  const selectedNode = selectedId
    ? nodes.find((n) => n.id === selectedId) ?? null
    : null

  const handleSearchSelect = (id: string) => {
    setSelectedId(id)
  }

  return (
    <div className="w-screen h-screen flex flex-col bg-surface">
      <header className="flex items-center gap-4 px-4 py-3 border-b border-border shrink-0">
        <SearchBar
          nodes={nodes}
          value={searchQuery}
          onChange={setSearchQuery}
          onSelectNode={handleSearchSelect}
        />
        <h1 className="text-sm font-semibold text-text-secondary ml-auto">
          CompanyBrain
        </h1>
      </header>

      <div className="flex flex-1 min-h-0">
        <div className="flex-1 min-w-0">
          <GraphView
            nodes={nodes}
            edges={edges}
            selectedId={selectedId}
            onSelect={setSelectedId}
            searchQuery={searchQuery}
          />
        </div>

        <SidePanel
          node={selectedNode}
          edges={edges}
          allNodes={nodes}
          onClose={() => setSelectedId(null)}
        />
      </div>
    </div>
  )
}
