import { useEffect, useState, useCallback } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { getGraph } from '../api'
import type { AnalysisData } from '../api'

interface Props {
  refreshKey?: number
  analysis?: AnalysisData | null
}

/* Node colour palette — matches the Biophilic design token set */
const NODE_PALETTE = [
  '#8b9d83', // primary-container  (sage)
  '#919e65', // tertiary-container (ochre)
  '#7c3307', // secondary-container (terracotta)
  '#272c20', // surface-container-high (dark)
  '#b9ccb0', // primary
  '#bfcd8f', // tertiary
]

function buildLocalGraph(analysis: AnalysisData): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = []
  const edges: Edge[] = []
  const projectId = 'project-0'

  nodes.push({
    id: projectId,
    data: { label: analysis.project_info.name },
    position: { x: 400, y: 20 },
    style: { background: '#238636', color: '#fff', border: 'none', borderRadius: 10, padding: '7px 14px', fontSize: 11, fontWeight: 600, fontFamily: 'Plus Jakarta Sans, sans-serif' },
  })

  analysis.materials?.forEach((m, i) => {
    const id = `mat-${i}`
    nodes.push({ id, data: { label: m.name }, position: { x: i * 180, y: 140 },
      style: { background: '#d29922', color: '#10150b', border: 'none', borderRadius: 10, padding: '7px 14px', fontSize: 11, fontWeight: 600, fontFamily: 'Plus Jakarta Sans, sans-serif' } })
    edges.push({ id: `e-mat-${i}`, source: projectId, target: id, label: 'CONSISTS_OF', animated: true, style: { stroke: '#8b9d83', strokeWidth: 1.5 }, labelStyle: { fill: '#c4c8be', fontSize: 9 }, labelBgStyle: { fill: 'rgba(16,21,11,0.75)', rx: 4 } })
  })

  analysis.energy?.forEach((e, i) => {
    const id = `eng-${i}`
    nodes.push({ id, data: { label: e.type }, position: { x: i * 200, y: 280 },
      style: { background: '#f85149', color: '#fff', border: 'none', borderRadius: 10, padding: '7px 14px', fontSize: 11, fontWeight: 600, fontFamily: 'Plus Jakarta Sans, sans-serif' } })
    edges.push({ id: `e-eng-${i}`, source: projectId, target: id, label: 'POWERED_BY', animated: true, style: { stroke: '#8b9d83', strokeWidth: 1.5 }, labelStyle: { fill: '#c4c8be', fontSize: 9 }, labelBgStyle: { fill: 'rgba(16,21,11,0.75)', rx: 4 } })
  })

  analysis.transport?.forEach((t, i) => {
    const id = `trn-${i}`
    nodes.push({ id, data: { label: t.method }, position: { x: i * 200, y: 420 },
      style: { background: '#a371f7', color: '#fff', border: 'none', borderRadius: 10, padding: '7px 14px', fontSize: 11, fontWeight: 600, fontFamily: 'Plus Jakarta Sans, sans-serif' } })
    edges.push({ id: `e-trn-${i}`, source: projectId, target: id, label: 'SHIPPED_VIA', animated: true, style: { stroke: '#8b9d83', strokeWidth: 1.5 }, labelStyle: { fill: '#c4c8be', fontSize: 9 }, labelBgStyle: { fill: 'rgba(16,21,11,0.75)', rx: 4 } })
  })

  return { nodes, edges }
}

export default function GraphViz({ refreshKey, analysis }: Props) {
  const [nodes,   setNodes]   = useState<Node[]>([])
  const [edges,   setEdges]   = useState<Edge[]>([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(false)

  const loadGraph = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      const data = await getGraph()

      // Neo4j empty — build graph from local analysis data
      if (data.nodes.length === 0 && analysis) {
        const local = buildLocalGraph(analysis)
        setNodes(local.nodes)
        setEdges(local.edges)
        setLoading(false)
        return
      }

      const flowNodes: Node[] = data.nodes.map((n, i) => ({
        id:       n.id,
        data:     { label: n.label },
        position: {
          x: 80 + (i % 4) * 220,
          y: 60 + Math.floor(i / 4) * 100,
        },
        style: {
          background:   n.color || NODE_PALETTE[i % NODE_PALETTE.length],
          color:        '#10150b',
          border:       'none',
          borderRadius: 10,
          padding:      '7px 14px',
          fontSize:     11,
          fontWeight:   600,
          fontFamily:   'Plus Jakarta Sans, sans-serif',
          boxShadow:    '0 2px 8px rgba(0,0,0,0.25)',
        },
      }))

      const flowEdges: Edge[] = data.edges.map((e, i) => ({
        id:       `e${i}`,
        source:   e.source,
        target:   e.target,
        label:    e.label,
        animated: true,
        style:    { stroke: '#8b9d83', strokeWidth: 1.5, strokeDasharray: '5 3' },
        labelStyle: {
          fill:       '#c4c8be',
          fontSize:   9,
          fontFamily: 'Plus Jakarta Sans, sans-serif',
          fontWeight: 500,
        },
        labelBgStyle: {
          fill:    'rgba(16,21,11,0.75)',
          rx:      4,
        },
      }))

      setNodes(flowNodes)
      setEdges(flowEdges)
    } catch {
      setError(true)
      setNodes([])
      setEdges([])
    } finally {
      setLoading(false)
    }
  }, [analysis])

  useEffect(() => {
    loadGraph()
  }, [loadGraph, refreshKey])

  const GRAPH_STYLES = {
    background: 'var(--color-surface-container)',
    borderRadius: '0.75rem',
    height: '100%',
  }

  /* ── Loading ── */
  if (loading) {
    return (
      <div className="card h-[480px] flex flex-col items-center justify-center gap-3">
        <svg className="animate-spin w-6 h-6 text-primary" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p className="text-sm text-on-surface-variant">Loading supply chain graph…</p>
      </div>
    )
  }

  /* ── Empty State ── */
  if (nodes.length === 0) {
    return (
      <div className="card h-[480px] flex flex-col items-center justify-center gap-4 text-center">
        <div className="noise-bg" />
        <div className="relative z-10 space-y-3">
          <div className="w-16 h-16 rounded-2xl bg-surface-container-highest flex items-center justify-center mx-auto">
            <span
              className="material-symbols-outlined text-on-surface-variant/50"
              style={{ fontSize: 32 }}
            >
              hub
            </span>
          </div>
          <div>
            <p className="text-sm font-semibold text-on-surface" style={{ fontFamily: 'Literata, serif' }}>
              Supply Chain Graph
            </p>
            <p className="text-xs text-on-surface-variant/60 mt-1 max-w-[200px] mx-auto leading-relaxed">
              {error
                ? 'Could not load graph data. Check backend connection.'
                : 'Upload a PDF to visualize your supply chain network.'}
            </p>
          </div>
          {error && (
            <button
              onClick={loadGraph}
              className="text-xs px-4 py-2 bg-surface-container border border-surface-container-highest text-on-surface-variant rounded-lg hover:text-primary hover:border-primary/30 transition-all duration-150 cursor-pointer"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    )
  }

  /* ── Graph ── */
  return (
    <div className="card h-[480px] overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        defaultEdgeOptions={{ type: 'smoothstep' }}
        style={GRAPH_STYLES}
      >
        <Background
          color="#31372a"
          gap={20}
          size={1}
          style={{ opacity: 0.6 }}
        />
        <Controls
          style={{
            background:   'var(--color-surface-container)',
            border:       '1px solid var(--color-surface-container-highest)',
            borderRadius: 10,
            boxShadow:    'none',
          }}
        />
        <MiniMap
          nodeColor={(n) => (n.style as any)?.background || '#8b9d83'}
          style={{
            background:   'var(--color-surface-container-low)',
            border:       '1px solid var(--color-surface-container-highest)',
            borderRadius: 10,
          }}
          maskColor="rgba(16, 21, 11, 0.75)"
        />
      </ReactFlow>
    </div>
  )
}
