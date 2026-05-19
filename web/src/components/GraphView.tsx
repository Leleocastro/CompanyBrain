import { useEffect, useRef, useCallback, useMemo } from 'react'
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
} from 'd3-force'
import { GraphNode, GraphEdge, NodeType } from '../types'

interface Props {
  nodes: GraphNode[]
  edges: GraphEdge[]
  selectedId: string | null
  onSelect: (id: string | null) => void
  searchQuery: string
}

interface SimNode extends GraphNode {
  x: number
  y: number
  vx: number
  vy: number
  fx?: number
  fy?: number
}

interface SimLink {
  source: string
  target: string
  label: string
  weight: number
}

const NODE_RADIUS = 22
const NODE_COLORS: Record<NodeType, string> = {
  Person: '#4f8',
  Document: '#48f',
  Repository: '#f84',
  Conversation: '#f48',
  Entity: '#84f',
  CodeFile: '#8f4',
}
const NODE_ICONS: Record<NodeType, string> = {
  Person: '\u{1F464}',
  Document: '\u{1F4C4}',
  Repository: '\u{1F4E6}',
  Conversation: '\u{1F4AC}',
  Entity: '\u{1F3F7}\uFE0F',
  CodeFile: '\u{1F4C1}',
}

function getNeighborIds(nodeId: string, edges: GraphEdge[]): Set<string> {
  const ids = new Set<string>([nodeId])
  for (const e of edges) {
    if (e.source === nodeId) ids.add(e.target)
    if (e.target === nodeId) ids.add(e.source)
  }
  return ids
}

export default function GraphView({ nodes, edges, selectedId, onSelect, searchQuery }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const viewportRef = useRef<SVGGElement>(null)
  const zoomRef = useRef({ x: 0, y: 0, k: 1 })
  const dragRef = useRef<{ nodeId: string; simNode: SimNode; pointerId: number } | null>(null)
  const panRef = useRef<{ startX: number; startY: number; startZoomX: number; startZoomY: number; pointerId: number } | null>(null)
  const pointerDownPos = useRef<{ x: number; y: number } | null>(null)

  const simRef = useRef<{
    sim: ReturnType<typeof forceSimulation<SimNode>>
    simNodes: SimNode[]
    simLinks: SimLink[]
  } | null>(null)

  const neighborIds = useMemo(
    () => (selectedId ? getNeighborIds(selectedId, edges) : null),
    [selectedId, edges]
  )

  const updateViewport = useCallback(() => {
    const g = viewportRef.current
    if (!g) return
    const z = zoomRef.current
    g.setAttribute('transform', `translate(${z.x},${z.y}) scale(${z.k})`)
  }, [])

  const tick = useCallback(() => {
    const svg = svgRef.current
    if (!svg) return
    const sim = simRef.current
    if (!sim) return

    const linksGroup = svg.querySelector('#links')!
    const nodesGroup = svg.querySelector('#nodes')!

    const linkEls = linksGroup.querySelectorAll<SVGLineElement>('.link-line')
    const labelEls = linksGroup.querySelectorAll<SVGTextElement>('.link-label')
    const nodeEls = nodesGroup.querySelectorAll<SVGGElement>('.node-group')
    const textEls = nodesGroup.querySelectorAll<SVGTextElement>('.node-text')

    const { simLinks, simNodes } = sim

    linkEls.forEach((el, i) => {
      const l = simLinks[i] as SimLink & { source: SimNode; target: SimNode }
      if (!l) return
      el.setAttribute('x1', String(l.source.x))
      el.setAttribute('y1', String(l.source.y))
      el.setAttribute('x2', String(l.target.x))
      el.setAttribute('y2', String(l.target.y))
    })

    labelEls.forEach((el, i) => {
      const l = simLinks[i] as SimLink & { source: SimNode; target: SimNode }
      if (!l) return
      const mx = (l.source.x + l.target.x) / 2
      const my = (l.source.y + l.target.y) / 2
      el.setAttribute('x', String(mx))
      el.setAttribute('y', String(my - 4))
    })

    nodeEls.forEach((el, i) => {
      const n = simNodes[i]
      if (!n) return
      el.setAttribute('transform', `translate(${n.x},${n.y})`)
    })

    textEls.forEach((el, i) => {
      const n = simNodes[i]
      if (!n) return
      el.setAttribute('x', String(n.x + NODE_RADIUS + 6))
      el.setAttribute('y', String(n.y + 4))
    })
  }, [])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const width = container.clientWidth
    const height = container.clientHeight

    const simNodes: SimNode[] = nodes.map((n) => ({
      ...n,
      x: width / 2 + (Math.random() - 0.5) * width * 0.4,
      y: height / 2 + (Math.random() - 0.5) * height * 0.4,
      vx: 0,
      vy: 0,
    }))

    const simLinks: SimLink[] = edges.map((e) => ({
      source: e.source,
      target: e.target,
      label: e.label,
      weight: e.weight,
    }))

    const sim = forceSimulation<SimNode>(simNodes)
      .force(
        'link',
        forceLink<SimNode, SimLink>(simLinks)
          .id((d) => d.id)
          .distance(120)
          .strength((l) => l.weight * 0.15)
      )
      .force('charge', forceManyBody().strength(-300))
      .force('center', forceCenter(width / 2, height / 2))
      .force('collide', forceCollide(NODE_RADIUS * 1.5))
      .alphaDecay(0.02)
      .on('tick', tick)

    simRef.current = { sim, simNodes, simLinks }
    zoomRef.current = { x: 0, y: 0, k: 1 }
    updateViewport()

    return () => {
      sim.stop()
    }
  }, [nodes, edges, tick, updateViewport])

  const handleNodeClick = useCallback(
    (id: string) => {
      onSelect(id === selectedId ? null : id)
    },
    [selectedId, onSelect]
  )

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const zoom = zoomRef.current
    const delta = -e.deltaY * 0.001
    const newK = Math.max(0.1, Math.min(10, zoom.k * (1 + delta)))

    const rect = svgRef.current!.getBoundingClientRect()
    const cx = e.clientX - rect.left
    const cy = e.clientY - rect.top

    zoom.x = cx - (cx - zoom.x) * (newK / zoom.k)
    zoom.y = cy - (cy - zoom.y) * (newK / zoom.k)
    zoom.k = newK

    updateViewport()
  }, [updateViewport])

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    pointerDownPos.current = { x: e.clientX, y: e.clientY }
    const nodeGroup = (e.target as Element).closest('.node-group') as SVGElement | null
    if (nodeGroup) {
      const nodeId = nodeGroup.getAttribute('data-node-id')
      if (!nodeId) return
      const sim = simRef.current
      if (!sim) return
      const simNode = sim.simNodes.find((n) => n.id === nodeId)
      if (!simNode) return
      nodeGroup.setPointerCapture(e.pointerId)
      simNode.fx = simNode.x
      simNode.fy = simNode.y
      sim.sim.alphaTarget(0.3).restart()
      dragRef.current = { nodeId, simNode, pointerId: e.pointerId }
    } else {
      const zoom = zoomRef.current
      panRef.current = {
        startX: e.clientX,
        startY: e.clientY,
        startZoomX: zoom.x,
        startZoomY: zoom.y,
        pointerId: e.pointerId,
      }
      ;(e.target as Element).setPointerCapture(e.pointerId)
    }
  }, [])

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (dragRef.current) {
      const svg = svgRef.current
      if (!svg) return
      const rect = svg.getBoundingClientRect()
      const zoom = zoomRef.current
      const x = (e.clientX - rect.left - zoom.x) / zoom.k
      const y = (e.clientY - rect.top - zoom.y) / zoom.k
      dragRef.current.simNode.fx = x
      dragRef.current.simNode.fy = y
    } else if (panRef.current) {
      const zoom = zoomRef.current
      zoom.x = panRef.current.startZoomX + (e.clientX - panRef.current.startX)
      zoom.y = panRef.current.startZoomY + (e.clientY - panRef.current.startY)
      updateViewport()
    }
  }, [updateViewport])

  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    if (dragRef.current) {
      const sim = simRef.current
      if (!sim) return
      const simNode = dragRef.current.simNode
      simNode.fx = undefined
      simNode.fy = undefined
      sim.sim.alphaTarget(0)
      const el = e.target as Element
      if (el.hasPointerCapture(dragRef.current.pointerId)) {
        el.releasePointerCapture(dragRef.current.pointerId)
      }
      dragRef.current = null
    } else if (panRef.current) {
      const el = e.target as Element
      if (el.hasPointerCapture(panRef.current.pointerId)) {
        el.releasePointerCapture(panRef.current.pointerId)
      }
      panRef.current = null
    }
    pointerDownPos.current = null
  }, [])

  const isDimmed = (nodeId: string): boolean => {
    if (!neighborIds) return false
    return !neighborIds.has(nodeId)
  }

  const isLinkDimmed = (edge: GraphEdge): boolean => {
    if (!neighborIds || !selectedId) return false
    return edge.source !== selectedId && edge.target !== selectedId
  }

  const matchesSearch = (nodeId: string): boolean => {
    if (!searchQuery) return true
    const node = nodes.find((n) => n.id === nodeId)
    if (!node) return true
    const q = searchQuery.toLowerCase()
    return (
      node.label.toLowerCase().includes(q) ||
      node.summary.toLowerCase().includes(q)
    )
  }

  return (
    <div ref={containerRef} className="w-full h-full relative">
      <svg
        ref={svgRef}
        className="w-full h-full"
        onWheel={handleWheel}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onClick={(e) => {
          if ((e.target as Element) === svgRef.current) {
            onSelect(null)
          }
        }}
      >
        <defs>
          <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#585b70" />
          </marker>
        </defs>

        <g ref={viewportRef} id="viewport">
          <g id="links">
            {edges.map((e, i) => {
              const dimmed = isLinkDimmed(e)
              return (
                <g key={`link-${i}`}>
                  <line
                    className="link-line"
                    stroke={dimmed ? '#313244' : '#585b70'}
                    strokeWidth={e.weight * 1.5}
                    strokeOpacity={dimmed ? 0.15 : 0.6}
                    markerEnd="url(#arrowhead)"
                  />
                  <text
                    className="link-label"
                    fill={dimmed ? '#313244' : '#6c7086'}
                    fontSize="10"
                    textAnchor="middle"
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                  >
                    {e.label}
                  </text>
                </g>
              )
            })}
          </g>

          <g id="nodes">
            {nodes.map((n) => {
              const dimmed = isDimmed(n.id)
              const searched = matchesSearch(n.id)
              const isSelected = n.id === selectedId

              const opacity = dimmed ? 0.15 : searched ? 1 : 0.3
              const strokeWidth = isSelected ? 3 : dimmed ? 1 : 2
              const strokeColor = isSelected
                ? '#f5c2e7'
                : dimmed
                  ? '#313244'
                  : NODE_COLORS[n.type]

              return (
                <g
                  key={n.id}
                  className="node-group"
                  data-node-id={n.id}
                  style={{ cursor: 'grab' }}
                  onClick={(e) => {
                    e.stopPropagation()
                    const pos = pointerDownPos.current
                    if (
                      pos &&
                      (Math.abs(e.clientX - pos.x) > 5 ||
                        Math.abs(e.clientY - pos.y) > 5)
                    ) {
                      return
                    }
                    handleNodeClick(n.id)
                  }}
                >
                  <circle
                    r={NODE_RADIUS}
                    fill={NODE_COLORS[n.type]}
                    fillOpacity={opacity}
                    stroke={strokeColor}
                    strokeWidth={strokeWidth}
                  />
                  <text
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize="16"
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                    opacity={opacity}
                  >
                    {NODE_ICONS[n.type]}
                  </text>
                </g>
              )
            })}
          </g>

          <g id="labels">
            {nodes.map((n) => {
              const dimmed = isDimmed(n.id)
              const searched = matchesSearch(n.id)
              const opacity = dimmed ? 0.15 : searched ? 1 : 0.3

              return (
                <text
                  key={`label-${n.id}`}
                  className="node-text"
                  fill="#cdd6f4"
                  fontSize="12"
                  opacity={opacity}
                  style={{ pointerEvents: 'none', userSelect: 'none' }}
                >
                  {n.label}
                </text>
              )
            })}
          </g>
        </g>
      </svg>
    </div>
  )
}
