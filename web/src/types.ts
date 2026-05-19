export type NodeType = 'Person' | 'Document' | 'Repository' | 'Conversation' | 'Entity' | 'CodeFile'

export interface GraphNode {
  id: string
  label: string
  type: NodeType
  summary: string
  properties: Record<string, string>
}

export interface GraphEdge {
  source: string
  target: string
  label: string
  weight: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}
