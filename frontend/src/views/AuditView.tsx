import type { AnalysisData } from '../api'
import PdfUploader from '../components/PdfUploader'
import GraphViz from '../components/GraphViz'
import DataTable from '../components/DataTable'

interface Props {
  analysis: AnalysisData | null
  graphKey: number
  onAnalyzed: (data: AnalysisData) => void
}

export default function AuditView({ analysis, graphKey, onAnalyzed }: Props) {
  return (
    <div className="px-16 py-14 w-full flex flex-col gap-16">

      {/* ── Header ── */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-display-lg"
            style={{ fontFamily: 'Literata, Georgia, serif', color: '#e0e5d3' }}>
            Audit Configuration
          </h1>
          <p className="mt-3 text-xl max-w-2xl" style={{ color: '#c4c8be' }}>
            Upload documentation and configure the scope of the carbon footprint analysis across your supply chain tiers.
          </p>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          <div className="flex items-center gap-2 px-5 py-2.5 rounded-full border"
            style={{ background: '#1c2116', borderColor: '#444841' }}>
            <span className="w-2.5 h-2.5 rounded-full"
              style={{ background: analysis ? '#b9ccb0' : '#ffdbcc' }} />
            <span style={{ color: '#c4c8be', fontSize: 15 }}>
              {analysis ? 'Analysis Ready' : 'Draft Mode'}
            </span>
          </div>
        </div>
      </div>

      {/* ── Bento Grid: Uploader + Graph ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* Left: Data Sources / Uploader */}
        <div className="lg:col-span-1 rounded-2xl p-8 flex flex-col gap-5 relative overflow-hidden"
          style={{ background: '#1c2116', border: '1px solid #31372a' }}>
          <div className="noise-bg" />
          <div className="relative z-10 flex flex-col gap-5 h-full">
            <div className="flex justify-between items-center">
              <h3 style={{ fontFamily: 'Literata, Georgia, serif', color: '#e0e5d3', fontSize: 24, fontWeight: 500 }}>
                Data Sources
              </h3>
              <span className="material-symbols-outlined" style={{ color: '#8e9289', fontSize: 26 }}>upload_file</span>
            </div>
            <p style={{ color: '#c4c8be', fontSize: 16 }}>
              Upload vendor invoices, LCA PDFs, or raw material manifests to extract footprint data.
            </p>
            <div className="flex-1">
              <PdfUploader onAnalyzed={onAnalyzed} />
            </div>
          </div>
        </div>

        {/* Right: Supply Chain Topology */}
        <div className="lg:col-span-2 rounded-2xl flex flex-col overflow-hidden relative"
          style={{ background: '#1c2116', border: '1px solid #31372a', minHeight: 480 }}>
          <div className="noise-bg" />
          <div className="relative z-10 p-7 flex justify-between items-center"
            style={{ borderBottom: '1px solid #31372a', background: '#1c2116' }}>
            <div>
              <h3 style={{ fontFamily: 'Literata, Georgia, serif', color: '#e0e5d3', fontSize: 24, fontWeight: 500 }}>
                Supply Chain Topology
              </h3>
              <p style={{ color: '#8e9289', marginTop: 4, fontSize: 15 }}>
                Tier 1 &amp; 2 vendor relationships and emission flows.
              </p>
            </div>
          </div>
          <div className="relative z-10 flex-1" style={{ minHeight: 380 }}>
            <GraphViz refreshKey={graphKey} />
          </div>
        </div>
      </div>

      {/* ── Data Table (real data only) ── */}
      {analysis ? (
        <DataTable data={analysis} />
      ) : (
        <div className="rounded-2xl p-16 flex flex-col items-center gap-5 text-center"
          style={{ background: '#1c2116', border: '1px dashed #31372a' }}>
          <span className="material-symbols-outlined" style={{ fontSize: 48, color: '#31372a' }}>table_chart</span>
          <p style={{ color: '#444841', fontSize: 16, fontWeight: 500 }}>
            Material inventory will appear here after PDF analysis
          </p>
        </div>
      )}
    </div>
  )
}

