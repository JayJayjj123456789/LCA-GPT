import { useEffect, useRef, useState } from 'react'
import Plot from 'react-plotly.js'
import { getHotspotChart, getPieChart, getSankeyChart } from '../api'
import type { AnalysisData } from '../api'

interface Props {
  data: AnalysisData
}

// ── Scroll-reveal wrapper ─────────────────────────────────────────────────────
function SlideReveal({
  children,
  delay = 0,
}: {
  children: React.ReactNode
  delay?: number
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          observer.disconnect()
        }
      },
      { threshold: 0.08 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return (
    <div
      ref={ref}
      style={{
        opacity:    visible ? 1 : 0,
        transform:  visible ? 'translateY(0)' : 'translateY(32px)',
        transition: `opacity 0.55s cubic-bezier(0.22,1,0.36,1) ${delay}ms,
                     transform 0.55s cubic-bezier(0.22,1,0.36,1) ${delay}ms`,
      }}
    >
      {children}
    </div>
  )
}

// ── Chart card shell ──────────────────────────────────────────────────────────
function ChartCard({
  title, subtitle, accent = '#8b9d83', children, loading,
}: {
  title: string
  subtitle?: string
  accent?: string
  children: React.ReactNode
  loading?: boolean
}) {
  return (
    <div
      className="relative flex flex-col overflow-hidden"
      style={{
        background:   '#1c2116',
        border:       '1px solid rgba(68,72,65,0.5)',
        borderRadius: 20,
        transition:   'border-color 0.2s, box-shadow 0.2s',
      }}
      onMouseEnter={e => {
        const el = e.currentTarget as HTMLElement
        el.style.borderColor = `${accent}55`
        el.style.boxShadow   = `0 0 0 1px ${accent}18, 0 8px 32px rgba(0,0,0,0.28)`
      }}
      onMouseLeave={e => {
        const el = e.currentTarget as HTMLElement
        el.style.borderColor = 'rgba(68,72,65,0.5)'
        el.style.boxShadow   = 'none'
      }}
    >
      <div className="noise-bg" />

      {/* Accent top-bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0,
        height: 2,
        background: `linear-gradient(90deg, ${accent}cc, transparent)`,
        borderRadius: '20px 20px 0 0',
        zIndex: 20,
      }} />

      {/* Header */}
      <div
        className="relative z-10 flex items-center justify-between gap-3"
        style={{ padding: '18px 22px 14px', borderBottom: '1px solid rgba(68,72,65,0.35)' }}
      >
        <div>
          <h3 style={{
            fontFamily: 'Literata, Georgia, serif',
            fontSize: 16, fontWeight: 500, color: '#e0e5d3', lineHeight: 1.3,
          }}>
            {title}
          </h3>
          {subtitle && (
            <p style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: 12, color: '#8e9289', marginTop: 2 }}>
              {subtitle}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {loading && (
            <span style={{
              fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: 11, color: '#8e9289',
              display: 'flex', alignItems: 'center', gap: 5,
            }}>
              <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Loading
            </span>
          )}
          {/* Live chip */}
          <div style={{
            padding: '3px 10px', borderRadius: 99,
            background: `${accent}18`, border: `1px solid ${accent}33`,
            fontSize: 11, fontWeight: 600, color: accent,
            fontFamily: 'Plus Jakarta Sans, sans-serif', letterSpacing: '0.04em',
          }}>
            Live
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export default function Charts({ data }: Props) {
  const [hotspot,    setHotspot]    = useState<any>(null)
  const [hotAnim,    setHotAnim]    = useState<any>(null)   // animated bar state
  const [pie,        setPie]        = useState<any>(null)
  const [sankey,     setSankey]     = useState<any>(null)
  const [error,      setError]      = useState<string | null>(null)
  const [pieVisible, setPieVisible] = useState(false)
  const [skyVisible, setSkyVisible] = useState(false)

  const loadCharts = async () => {
    setError(null)
    setHotspot(null); setHotAnim(null)
    setPie(null); setSankey(null)
    setPieVisible(false); setSkyVisible(false)
    try {
      const [h, p, s] = await Promise.all([
        getHotspotChart(data.materials || []),
        getPieChart(data),
        getSankeyChart(data),
      ])
      // ── Bar: render at x=0 first, then animate to real values ──
      if (h?.data?.length) {
        const zeroData = h.data.map((trace: any) => ({
          ...trace,
          x: Array.isArray(trace.x) ? trace.x.map(() => 0) : trace.x,
        }))
        setHotspot({ ...h, data: zeroData })
        setTimeout(() => setHotAnim(h), 60)   // trigger Plotly transition
      } else {
        setHotspot(h)
      }
      // ── Pie: CSS fade after short delay ──
      setPie(p)
      setTimeout(() => setPieVisible(true), 120)
      // ── Sankey: CSS fade after longer delay ──
      setSankey(s)
      setTimeout(() => setSkyVisible(true), 220)
    } catch (err: any) {
      console.error('Chart loading failed:', err)
      setError(err?.message || 'Failed to load charts — restart the backend and try again.')
    }
  }

  useEffect(() => { loadCharts() }, [data])

  return (
    <div>
      <SectionTitle icon="bar_chart">Carbon Analytics</SectionTitle>

      {/* Error banner */}
      {error && (
        <div style={{
          marginBottom: 20, padding: '14px 20px', borderRadius: 14,
          background: 'rgba(198,107,61,0.1)', border: '1px solid rgba(198,107,61,0.3)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="material-symbols-outlined" style={{ fontSize: 18, color: '#c66b3d', fontVariationSettings: "'FILL' 1" }}>error</span>
            <span style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: 13, color: '#ffb694' }}>{error}</span>
          </div>
          <button
            onClick={loadCharts}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 14px', borderRadius: 8,
              background: 'rgba(198,107,61,0.15)', border: '1px solid rgba(198,107,61,0.4)',
              color: '#ffb694', fontSize: 12, fontWeight: 600,
              fontFamily: 'Plus Jakarta Sans, sans-serif', cursor: 'pointer', flexShrink: 0,
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>refresh</span>
            Retry
          </button>
        </div>
      )}

      {/* Top row — slide in with stagger */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">
        <div className="lg:col-span-2">
          <SlideReveal delay={0}>
            <ChartCard
              title="Carbon Hotspots by Material"
              subtitle="Emissions intensity per material (kgCO₂e)"
              accent="#c66b3d"
              loading={!hotspot && !error}
            >
              {hotspot ? (
                <Plot
                  data={(hotAnim ?? hotspot).data}
                  layout={{ ...hotspot.layout, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)' }}
                  style={{ width: '100%', height: 340 }}
                  config={{ displayModeBar: false, responsive: true }}
                />
              ) : (
                <Skeleton h={340} />
              )}
            </ChartCard>
          </SlideReveal>
        </div>

        <div>
          <SlideReveal delay={80}>
            <ChartCard
              title="Emissions Breakdown"
              subtitle="By lifecycle phase (%)"
              accent="#919e65"
              loading={!pie && !error}
            >
              {pie ? (
                <div style={{
                  opacity:   pieVisible ? 1 : 0,
                  transform: pieVisible ? 'scale(1)' : 'scale(0.94)',
                  transition: 'opacity 0.6s cubic-bezier(0.22,1,0.36,1), transform 0.6s cubic-bezier(0.22,1,0.36,1)',
                }}>
                  <Plot
                    data={pie.data}
                    layout={{ ...pie.layout, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)' }}
                    style={{ width: '100%', height: 340 }}
                    config={{ displayModeBar: false, responsive: true }}
                  />
                </div>
              ) : (
                <Skeleton h={340} />
              )}
            </ChartCard>
          </SlideReveal>
        </div>
      </div>

      {/* Sankey */}
      <SlideReveal delay={160}>
        <ChartCard
          title="Supply Chain Carbon Flow"
          subtitle="Sankey diagram — material, energy & transport flows weighted by CO₂e"
          accent="#b9ccb0"
          loading={!sankey && !error}
        >
          {sankey ? (
            <div style={{
              opacity:   skyVisible ? 1 : 0,
              transform: skyVisible ? 'translateY(0)' : 'translateY(16px)',
              transition: 'opacity 0.7s cubic-bezier(0.22,1,0.36,1), transform 0.7s cubic-bezier(0.22,1,0.36,1)',
            }}>
              <Plot
                data={sankey.data}
                layout={{
                  ...sankey.layout,
                  paper_bgcolor: 'rgba(0,0,0,0)',
                  plot_bgcolor:  'rgba(0,0,0,0)',
                  margin: { t: 16, b: 16, l: 16, r: 16 },
                }}
                style={{ width: '100%', height: 460 }}
                config={{ displayModeBar: false, responsive: true }}
              />
            </div>
          ) : (
            <Skeleton h={460} />
          )}
        </ChartCard>
      </SlideReveal>

    </div>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function Skeleton({ h }: { h: number }) {
  return (
    <div style={{
      height: h,
      borderRadius: 12,
      background: 'linear-gradient(90deg, #1c2116 25%, #272c20 50%, #1c2116 75%)',
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.5s infinite',
    }} />
  )
}

function SectionTitle({ icon, children }: { icon?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 mb-7">
      {icon && (
        <span className="material-symbols-outlined" style={{ fontSize: 20, color: '#8b9d83', fontVariationSettings: "'FILL' 1" }}>
          {icon}
        </span>
      )}
      <h2 style={{
        fontFamily: 'Plus Jakarta Sans, sans-serif',
        fontSize: 13, fontWeight: 700, letterSpacing: '0.08em',
        color: '#8e9289', textTransform: 'uppercase',
      }}>
        {children}
      </h2>
      <div className="flex-1 h-px" style={{ background: 'rgba(68,72,65,0.5)' }} />
    </div>
  )
}
