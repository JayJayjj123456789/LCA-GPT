import { useState } from 'react'
import type { AnalysisData } from '../api'
import type { NavView } from '../App'
import GraphViz from '../components/GraphViz'
import Charts from '../components/Charts'

interface Props {
  analysis: AnalysisData | null
  audits: AnalysisData[]
  graphKey: number
  onNavigate: (v: NavView) => void
}

export default function GraphView({ analysis, audits, graphKey, onNavigate }: Props) {
  // Default to the most recent audit (index 0) when multiple exist
  const [selectedIdx, setSelectedIdx] = useState(0)

  // Derive the active analysis: prefer from audits array (supports multi-doc),
  // fall back to the single `analysis` prop for backwards compatibility
  const activeList = audits.length > 0 ? audits : (analysis ? [analysis] : [])
  const activeAnalysis = activeList[selectedIdx] ?? null

  return (
    <div className="px-14 py-12 w-full flex flex-col gap-10">

      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-display-lg"
            style={{ fontFamily:'Literata, serif', color:'#e0e5d3' }}>
            Supply Chain Graph
          </h1>
          <p className="mt-2 text-lg" style={{ color:'#c4c8be' }}>
            Interactive visualization of your supply chain node network.
          </p>
        </div>
        <div className="flex gap-2">
          <button className="p-2 rounded-md cursor-pointer"
            style={{ background:'#272c20', color:'#e0e5d3', border:'1px solid #31372a' }}>
            <span className="material-symbols-outlined" style={{ fontSize:20 }}>zoom_in</span>
          </button>
          <button className="p-2 rounded-md cursor-pointer"
            style={{ background:'#272c20', color:'#e0e5d3', border:'1px solid #31372a' }}>
            <span className="material-symbols-outlined" style={{ fontSize:20 }}>zoom_out</span>
          </button>
        </div>
      </div>

      {/* Document selector — only shown when there are multiple uploads */}
      {activeList.length > 1 && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined" style={{ fontSize:16, color:'#8e9289' }}>folder_open</span>
            <span className="text-xs font-semibold uppercase tracking-wider" style={{ color:'#8e9289' }}>
              Uploaded Documents — {activeList.length} total
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {activeList.map((a, i) => (
              <button
                key={i}
                onClick={() => setSelectedIdx(i)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all duration-150 cursor-pointer border"
                style={
                  i === selectedIdx
                    ? { background:'#8b9d83', color:'#10150b', borderColor:'#8b9d83' }
                    : { background:'#1c2116', color:'#c4c8be', borderColor:'#31372a' }
                }
              >
                <span className="material-symbols-outlined" style={{ fontSize:14 }}>description</span>
                {a.project_info?.name || `Document ${i + 1}`}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Full-width graph */}
      <div className="rounded-xl overflow-hidden relative"
        style={{ background:'#1c2116', border:'1px solid #31372a', height:560 }}>
        <div className="noise-bg" />
        <div className="relative z-10 h-full">
          <GraphViz refreshKey={graphKey + selectedIdx} analysis={activeAnalysis} />
        </div>
      </div>

      {/* Charts below if data exists */}
      {activeAnalysis ? (
        <Charts data={activeAnalysis} />
      ) : (
        <div className="text-center py-12 rounded-xl"
          style={{ background:'#1c2116', border:'1px solid #31372a' }}>
          <span className="material-symbols-outlined" style={{ fontSize:40, color:'#31372a' }}>analytics</span>
          <p className="text-sm mt-3" style={{ color:'#8e9289' }}>
            Run a carbon audit to see emissions data in the charts below.
          </p>
          <button onClick={() => onNavigate('audit')}
            className="mt-4 px-6 py-2.5 rounded-xl text-xs font-semibold uppercase tracking-widest cursor-pointer"
            style={{ background:'#8b9d83', color:'#101f0d' }}>
            Go to Audit Tool
          </button>
        </div>
      )}
    </div>
  )
}
