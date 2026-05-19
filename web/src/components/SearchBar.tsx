import { useState, useRef, useEffect } from 'react'
import { GraphNode } from '../types'

interface Props {
  nodes: GraphNode[]
  value: string
  onChange: (value: string) => void
  onSelectNode: (id: string) => void
}

export default function SearchBar({ nodes, value, onChange, onSelectNode }: Props) {
  const [focused, setFocused] = useState(false)
  const [highlightedIdx, setHighlightedIdx] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)

  const filtered = value.trim()
    ? nodes.filter(
        (n) =>
          n.label.toLowerCase().includes(value.toLowerCase()) ||
          n.summary.toLowerCase().includes(value.toLowerCase())
      )
    : []

  useEffect(() => {
    setHighlightedIdx(-1)
  }, [value])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlightedIdx((prev) => Math.min(prev + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlightedIdx((prev) => Math.max(prev - 1, 0))
    } else if (e.key === 'Enter' && highlightedIdx >= 0 && filtered[highlightedIdx]) {
      onSelectNode(filtered[highlightedIdx].id)
      onChange('')
      inputRef.current?.blur()
    } else if (e.key === 'Escape') {
      setFocused(false)
      inputRef.current?.blur()
    }
  }

  return (
    <div className="relative w-full max-w-md">
      <div className="flex items-center gap-2 bg-surface-alt border border-border rounded-lg px-3 py-2 focus-within:border-accent-blue transition-colors">
        <span className="text-text-muted">🔍</span>
        <input
          ref={inputRef}
          type="text"
          placeholder="Buscar nós..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 150)}
          onKeyDown={handleKeyDown}
          className="bg-transparent text-text-primary placeholder-text-muted outline-none flex-1 text-sm"
        />
        {value && (
          <button
            onClick={() => onChange('')}
            className="text-text-muted hover:text-text-primary text-sm"
          >
            ✕
          </button>
        )}
      </div>

      {focused && filtered.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-surface-alt border border-border rounded-lg shadow-lg overflow-hidden z-50">
          {filtered.map((n, i) => (
            <button
              key={n.id}
              onMouseDown={(e) => {
                e.preventDefault()
                onSelectNode(n.id)
                onChange('')
              }}
              onMouseEnter={() => setHighlightedIdx(i)}
              className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition-colors ${
                i === highlightedIdx ? 'bg-surface-hover' : ''
              }`}
            >
              <span className="shrink-0 text-base">
                {n.type === 'Person' && '\u{1F464}'}
                {n.type === 'Document' && '\u{1F4C4}'}
                {n.type === 'Repository' && '\u{1F4E6}'}
                {n.type === 'Conversation' && '\u{1F4AC}'}
                {n.type === 'Entity' && '\u{1F3F7}\uFE0F'}
                {n.type === 'CodeFile' && '\u{1F4C1}'}
              </span>
              <span className="text-text-primary truncate">{n.label}</span>
              <span className="text-text-muted text-xs ml-auto shrink-0">{n.type}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
