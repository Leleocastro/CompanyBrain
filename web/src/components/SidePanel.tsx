import { GraphNode, GraphEdge, NodeType } from '../types'

interface Props {
  node: GraphNode | null
  edges: GraphEdge[]
  allNodes: GraphNode[]
  onClose: () => void
}

const NODE_ICONS: Record<NodeType, string> = {
  Person: '\u{1F464}',
  Document: '\u{1F4C4}',
  Repository: '\u{1F4E6}',
  Conversation: '\u{1F4AC}',
  Entity: '\u{1F3F7}\uFE0F',
  CodeFile: '\u{1F4C1}',
}

const NODE_COLORS: Record<NodeType, string> = {
  Person: '#4f8',
  Document: '#48f',
  Repository: '#f84',
  Conversation: '#f48',
  Entity: '#84f',
  CodeFile: '#8f4',
}

export default function SidePanel({ node, edges, allNodes, onClose }: Props) {
  if (!node) {
    return (
      <div className="w-80 bg-surface-alt border-l border-border p-4 flex items-center justify-center text-text-muted text-sm">
        Selecione um nó no grafo para ver detalhes
      </div>
    )
  }

  const connectedEdges = edges.filter(
    (e) => e.source === node.id || e.target === node.id
  )

  const connectedNodes = connectedEdges.map((e) => {
    const neighborId = e.source === node.id ? e.target : e.source
    const neighbor = allNodes.find((n) => n.id === neighborId)
    return { edge: e, neighbor }
  })

  return (
    <div className="w-80 bg-surface-alt border-l border-border overflow-y-auto flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-xl">{NODE_ICONS[node.type]}</span>
          <h2 className="font-semibold text-text-primary truncate">{node.label}</h2>
        </div>
        <button
          onClick={onClose}
          className="text-text-muted hover:text-text-primary text-lg leading-none p-1"
        >
          ✕
        </button>
      </div>

      <div className="p-4 space-y-4">
        <div>
          <span
            className="inline-block px-2 py-0.5 rounded text-xs font-medium"
            style={{
              backgroundColor: `${NODE_COLORS[node.type]}22`,
              color: NODE_COLORS[node.type],
            }}
          >
            {node.type}
          </span>
        </div>

        <p className="text-sm text-text-secondary leading-relaxed">
          {node.summary}
        </p>

        {Object.keys(node.properties).length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
              Propriedades
            </h3>
            <div className="space-y-1">
              {Object.entries(node.properties).map(([key, val]) => (
                <div key={key} className="flex justify-between text-sm">
                  <span className="text-text-muted">{key}</span>
                  <span className="text-text-primary">{val}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {connectedNodes.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
              Conexões ({connectedNodes.length})
            </h3>
            <div className="space-y-2">
              {connectedNodes.map(({ edge, neighbor }, i) => {
                if (!neighbor) return null
                return (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <span>{NODE_ICONS[neighbor.type]}</span>
                    <span className="text-text-primary truncate">{neighbor.label}</span>
                    <span className="text-text-muted text-xs ml-auto shrink-0">
                      {edge.label}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
