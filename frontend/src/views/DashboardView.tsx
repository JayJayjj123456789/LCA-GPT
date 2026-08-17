import type { AnalysisData } from '../api'
import type { NavView } from '../App'
import Dashboard from '../components/Dashboard'
import Charts from '../components/Charts'

interface Props {
  analysis: AnalysisData | null
  onNavigate: (v: NavView) => void
}

export default function DashboardView({ analysis, onNavigate }: Props) {
  const today = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

  return (
    <div style={{ padding: '56px 64px', width: '100%', display: 'flex', flexDirection: 'column', gap: 56 }}>

      {/* ── Hero Header ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: 24 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 24, height: 2, background: '#8b9d83', borderRadius: 99 }} />
            <span style={{
              fontFamily: 'Plus Jakarta Sans, sans-serif',
              fontSize: 12, fontWeight: 700, letterSpacing: '0.1em',
              color: '#8b9d83', textTransform: 'uppercase',
            }}>
              FY24 Carbon Audit Platform
            </span>
          </div>
          <h1 style={{
            fontFamily: 'Literata, Georgia, serif',
            fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
            fontWeight: 700, letterSpacing: '-0.02em',
            color: '#e0e5d3', lineHeight: 1.1,
          }}>
            {analysis?.project_info?.name || 'Overview'}
          </h1>
          <p style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: 15, color: '#8e9289', lineHeight: 1.5 }}>
            System-wide environmental impact summary.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexShrink: 0 }}>
          {analysis && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 7,
              padding: '8px 16px', borderRadius: 99,
              background: 'rgba(139,157,131,0.12)', border: '1px solid rgba(139,157,131,0.25)',
            }}>
              <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#b9ccb0', boxShadow: '0 0 6px #b9ccb066' }} />
              <span style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: 13, color: '#b9ccb0', fontWeight: 500 }}>
                Analysis Ready
              </span>
            </div>
          )}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 7,
            padding: '8px 16px', borderRadius: 12,
            background: '#1c2116', border: '1px solid rgba(68,72,65,0.5)',
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: 16, color: '#8e9289' }}>calendar_month</span>
            <span style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: 13, color: '#c4c8be' }}>{today}</span>
          </div>
        </div>
      </div>

      {/* ── Content ── */}
      {analysis ? (
        <>
          <Dashboard data={analysis} />
          <Charts data={analysis} />

          {/* Latest summary */}
          <section>
            <div style={{
              borderRadius: 20, padding: '32px 36px',
              position: 'relative', overflow: 'hidden',
              background: '#1c2116', border: '1px solid rgba(68,72,65,0.5)',
            }}>
              <div className="noise-bg" />
              <div style={{
                position: 'absolute', top: 0, left: 0, right: 0, height: 2,
                background: 'linear-gradient(90deg, #b9ccb0aa, transparent)',
                borderRadius: '20px 20px 0 0',
              }} />
              <div style={{ position: 'relative', zIndex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                  <h3 style={{ fontFamily: 'Literata, Georgia, serif', fontSize: 22, fontWeight: 500, color: '#e0e5d3' }}>
                    Latest Audit Summary
                  </h3>
                  <button
                    onClick={() => onNavigate('reports')}
                    style={{
                      fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: 14, color: '#8b9d83',
                      background: 'none', border: 'none', cursor: 'pointer',
                      display: 'flex', alignItems: 'center', gap: 4,
                    }}
                  >
                    View Reports
                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>arrow_forward</span>
                  </button>
                </div>
                <p style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: 15, lineHeight: 1.7, color: '#c4c8be' }}>
                  {analysis.summary || 'No summary available.'}
                </p>
                {analysis.recommendations?.length > 0 && (
                  <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {analysis.recommendations.slice(0, 3).map((rec, i) => (
                      <div key={i} style={{
                        display: 'flex', alignItems: 'flex-start', gap: 14,
                        padding: '14px 18px', borderRadius: 14,
                        background: '#272c20', border: '1px solid rgba(68,72,65,0.4)',
                      }}>
                        <span className="material-symbols-outlined" style={{ fontSize: 18, color: '#8b9d83', fontVariationSettings: "'FILL' 1", flexShrink: 0, marginTop: 2 }}>
                          lightbulb
                        </span>
                        <p style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: 14, color: '#c4c8be', lineHeight: 1.6 }}>
                          {rec}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </section>
        </>
      ) : (
        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          minHeight: '55vh', gap: 32, textAlign: 'center',
        }}>
          <div style={{
            width: 96, height: 96, borderRadius: '50%',
            background: 'rgba(139,157,131,0.08)', border: '1px solid rgba(139,157,131,0.2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: 40, color: '#8b9d83', fontVariationSettings: "'FILL' 1" }}>
              eco
            </span>
          </div>
          <div style={{ maxWidth: 440 }}>
            <h2 style={{ fontFamily: 'Literata, Georgia, serif', fontSize: 24, fontWeight: 600, color: '#e0e5d3', marginBottom: 10 }}>
              No Active Audit
            </h2>
            <p style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: 14, color: '#8e9289', lineHeight: 1.6 }}>
              Upload a supply chain PDF document to run an AI-powered carbon footprint analysis.
            </p>
          </div>
          <button
            onClick={() => onNavigate('audit')}
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '13px 28px', borderRadius: 14,
              background: '#b9ccb0', color: '#253421',
              fontSize: 14, fontWeight: 700, fontFamily: 'Plus Jakarta Sans, sans-serif',
              border: 'none', cursor: 'pointer',
            }}
            onMouseEnter={e => ((e.currentTarget as HTMLElement).style.opacity = '0.88')}
            onMouseLeave={e => ((e.currentTarget as HTMLElement).style.opacity = '1')}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 20 }}>upload_file</span>
            Start New Audit
          </button>
        </div>
      )}
    </div>
  )
}
