import { useState, useEffect, useRef } from 'react'
import Plot from 'react-plotly.js'
import {
  runMatrixLCA,
  runMonteCarlo,
  runSensitivity,
  runNonLinear,
  getTornadoChart,
  getMonteCarloChart,
  getWaterfallChart,
  type AnalysisData,
  type ChartData,
} from '../api'

interface Props {
  analysis: AnalysisData | null
}

type Tab = 'matrix' | 'montecarlo' | 'sensitivity' | 'nonlinear'

export default function LiveDemoView({ analysis }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('matrix')
  const [matrixResult, setMatrixResult] = useState<any>(null)
  const [mcResult, setMcResult] = useState<any>(null)
  const [sensResult, setSensResult] = useState<any>(null)
  const [nlResult, setNlResult] = useState<any>(null)
  const [tornadoChart, setTornadoChart] = useState<ChartData | null>(null)
  const [mcChart, setMcChart] = useState<ChartData | null>(null)
  const [waterfallChart, setWaterfallChart] = useState<ChartData | null>(null)
  const [loading, setLoading] = useState(false)
  const [timer, setTimer] = useState(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Timer for live demo
  useEffect(() => {
    if (loading) {
      const start = Date.now()
      timerRef.current = setInterval(() => {
        setTimer((Date.now() - start) / 1000)
      }, 50)
    } else {
      if (timerRef.current) clearInterval(timerRef.current)
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [loading])

  const runAll = async () => {
    if (!analysis) return
    setLoading(true)
    setTimer(0)
    try {
      const [matrix, mc, sens, nl, tornado, mcHist, waterfall] = await Promise.all([
        runMatrixLCA(analysis),
        runMonteCarlo(analysis, 5000, 0.15),
        runSensitivity(analysis),
        runNonLinear(analysis),
        getTornadoChart(analysis),
        getMonteCarloChart(analysis),
        getWaterfallChart(analysis),
      ])
      setMatrixResult(matrix)
      setMcResult(mc)
      setSensResult(sens)
      setNlResult(nl)
      setTornadoChart(tornado)
      setMcChart(mcHist)
      setWaterfallChart(waterfall)
    } catch (e: any) {
      console.error('Live demo error:', e)
    } finally {
      setLoading(false)
    }
  }

  const tabs: { key: Tab; label: string; icon: string }[] = [
    { key: 'matrix', label: 'Matrix LCA', icon: '🔢' },
    { key: 'montecarlo', label: 'Monte Carlo', icon: '🎲' },
    { key: 'sensitivity', label: 'Sensitivity', icon: '📊' },
    { key: 'nonlinear', label: 'Non-Linear', icon: '📈' },
  ]

  return (
    <div className="p-6 md:p-10 max-w-[1400px] mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">⚡</span>
          <h1 className="font-serif text-2xl md:text-3xl" style={{ color: '#e0e5d3' }}>
            Live Mathematical Analysis
          </h1>
        </div>
        <p style={{ color: '#8e9289' }} className="text-sm">
          Real-time computation: h = Q · B · A⁻¹ · f — Heijungs & Suh Framework
        </p>
      </div>

      {/* Timer + Run Button */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={runAll}
          disabled={!analysis || loading}
          className="px-6 py-3 rounded-xl font-medium transition-all duration-300"
          style={{
            background: analysis && !loading
              ? 'linear-gradient(135deg, #919e65, #b9ccb0)'
              : '#272c20',
            color: analysis && !loading ? '#10150b' : '#8e9289',
            cursor: analysis && !loading ? 'pointer' : 'not-allowed',
            opacity: loading ? 0.7 : 1,
          }}
        >
          {loading ? '⏳ Computing...' : '▶ Run Full Analysis'}
        </button>

        {/* Timer Display */}
        <div
          className="px-5 py-3 rounded-xl font-mono text-lg"
          style={{
            background: '#1c2116',
            border: '1px solid #31372a',
            color: loading ? '#bfcd8f' : '#b9ccb0',
            minWidth: 140,
            textAlign: 'center',
          }}
        >
          {timer.toFixed(2)}s
        </div>

        {/* Comparison */}
        {!loading && matrixResult && (
          <div
            className="px-4 py-2 rounded-lg text-sm"
            style={{ background: 'rgba(145,158,101,0.15)', color: '#bfcd8f' }}
          >
            Traditional LCA: ~21 days · AI-LCA: {timer.toFixed(2)}s · <strong>{Math.round(21 * 24 * 3600 / Math.max(timer, 0.01))}x faster</strong>
          </div>
        )}
      </div>

      {!analysis && (
        <div
          className="rounded-2xl p-12 text-center"
          style={{ background: '#1c2116', border: '1px solid #272c20' }}
        >
          <p className="text-4xl mb-4">📄</p>
          <p style={{ color: '#8e9289' }}>
            Upload a PDF in the <strong>Audit</strong> tab first to run the mathematical analysis.
          </p>
        </div>
      )}

      {analysis && matrixResult && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <KPICard
              label="Total Impact"
              value={`${matrixResult.total_impact?.toFixed(1) || '—'}`}
              unit="kg CO₂-eq"
              icon="🌍"
            />
            <KPICard
              label="95% Confidence"
              value={mcResult ? `${mcResult.ci_95[0]?.toFixed(0)} – ${mcResult.ci_95[1]?.toFixed(0)}` : '—'}
              unit="kg CO₂-eq"
              icon="📐"
            />
            <KPICard
              label="Non-Linear Deviation"
              value={nlResult ? `${nlResult.deviation_percent?.toFixed(1)}%` : '—'}
              unit="from linear"
              icon="📈"
            />
            <KPICard
              label="Top Hotspot"
              value={matrixResult.hotspots?.[0]?.process?.slice(0, 18) || '—'}
              unit={`${matrixResult.hotspots?.[0]?.percentage?.toFixed(0) || 0}% of total`}
              icon="🔥"
            />
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            {tabs.map(t => (
              <button
                key={t.key}
                onClick={() => setActiveTab(t.key)}
                className="px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all"
                style={{
                  background: activeTab === t.key ? 'rgba(145,158,101,0.2)' : '#1c2116',
                  border: `1px solid ${activeTab === t.key ? '#919e65' : '#272c20'}`,
                  color: activeTab === t.key ? '#bfcd8f' : '#8e9289',
                }}
              >
                {t.icon} {t.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="space-y-6">
            {activeTab === 'matrix' && (
              <>
                {/* Matrix Result */}
                <Card title="🔢 Heijungs Matrix Framework: h = Q · B · A⁻¹ · f">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <MatrixDisplay
                      label="Scaling Vector (s = A⁻¹·f)"
                      data={matrixResult.scaling_vector}
                    />
                    <MatrixDisplay
                      label="Inventory (g = B·s)"
                      data={matrixResult.inventory}
                    />
                    <MatrixDisplay
                      label="Impact (h = Q·g)"
                      data={matrixResult.impact_indicators}
                    />
                  </div>
                </Card>

                {/* Hotspots */}
                <Card title="🔥 Process Hotspot Analysis">
                  <div className="space-y-2">
                    {(matrixResult.hotspots || []).map((h: any, i: number) => (
                      <div key={i} className="flex items-center gap-3">
                        <div className="text-sm font-mono w-8" style={{ color: '#8e9289' }}>
                          #{i + 1}
                        </div>
                        <div className="flex-1">
                          <div className="flex justify-between mb-1">
                            <span className="text-sm" style={{ color: '#e0e5d3' }}>
                              {h.process}
                            </span>
                            <span className="text-sm font-mono" style={{ color: '#bfcd8f' }}>
                              {h.impact.toFixed(1)} kg CO₂-eq ({h.percentage}%)
                            </span>
                          </div>
                          <div className="h-2 rounded-full overflow-hidden" style={{ background: '#272c20' }}>
                            <div
                              className="h-full rounded-full transition-all duration-700"
                              style={{
                                width: `${h.percentage}%`,
                                background: `linear-gradient(90deg, #919e65, ${i === 0 ? '#c66b3d' : '#b9ccb0'})`,
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>

                {/* Waterfall */}
                {waterfallChart && (
                  <Card title="📊 Cumulative Emissions Waterfall">
                    <Plot
                      data={waterfallChart.data}
                      layout={{ ...waterfallChart.layout, autosize: true }}
                      config={{ displayModeBar: false, responsive: true }}
                      style={{ width: '100%', height: 400 }}
                    />
                  </Card>
                )}
              </>
            )}

            {activeTab === 'montecarlo' && mcResult && (
              <>
                <Card title="🎲 Monte Carlo Uncertainty (N = 5,000)">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <Stat label="Mean" value={mcResult.mean?.toFixed(1)} unit="kg CO₂-eq" />
                    <Stat label="Std Dev" value={mcResult.std?.toFixed(1)} unit="σ" />
                    <Stat label="95% CI Low" value={mcResult.ci_95?.[0]?.toFixed(1)} unit="kg CO₂-eq" />
                    <Stat label="95% CI High" value={mcResult.ci_95?.[1]?.toFixed(1)} unit="kg CO₂-eq" />
                  </div>
                </Card>

                {mcChart && (
                  <Card title="📊 Impact Distribution">
                    <Plot
                      data={mcChart.data}
                      layout={{ ...mcChart.layout, autosize: true }}
                      config={{ displayModeBar: false, responsive: true }}
                      style={{ width: '100%', height: 380 }}
                    />
                  </Card>
                )}

                {/* Convergence */}
                {mcResult.convergence && mcResult.convergence.length > 0 && (
                  <Card title="📈 Convergence Analysis">
                    <div className="space-y-1">
                      {mcResult.convergence.map((c: any, i: number) => (
                        <div key={i} className="flex justify-between text-sm font-mono"
                          style={{ color: '#c4c8be' }}>
                          <span>N = {c.n}</span>
                          <span>μ = {c.mean?.toFixed(1)}</span>
                          <span>σ = {c.std?.toFixed(1)}</span>
                          <span>95% CI: [{c.ci_95_low?.toFixed(0)}, {c.ci_95_high?.toFixed(0)}]</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
              </>
            )}

            {activeTab === 'sensitivity' && sensResult && (
              <>
                {tornadoChart && (
                  <Card title="🌪️ Tornado Diagram (±10% Variation)">
                    <Plot
                      data={tornadoChart.data}
                      layout={{ ...tornadoChart.layout, autosize: true }}
                      config={{ displayModeBar: false, responsive: true }}
                      style={{ width: '100%', height: 400 }}
                    />
                  </Card>
                )}

                <Card title="📊 Contribution Analysis">
                  <div className="space-y-2">
                    {(sensResult.contributions || []).slice(0, 10).map((c: any, i: number) => (
                      <div key={i} className="flex items-center gap-3">
                        <div className="text-sm font-mono w-8" style={{ color: '#8e9289' }}>
                          #{i + 1}
                        </div>
                        <div className="flex-1">
                          <div className="flex justify-between mb-1">
                            <span className="text-sm" style={{ color: '#e0e5d3' }}>
                              {c.process}
                            </span>
                            <span className="text-sm font-mono" style={{ color: '#bfcd8f' }}>
                              {c.impact?.toFixed(1)} ({c.percentage}%)
                            </span>
                          </div>
                          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: '#272c20' }}>
                            <div
                              className="h-full rounded-full"
                              style={{
                                width: `${c.percentage}%`,
                                background: 'linear-gradient(90deg, #919e65, #bfcd8f)',
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </>
            )}

            {activeTab === 'nonlinear' && nlResult && (
              <>
                <Card title="📈 Linear vs Non-Linear Comparison">
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <Stat label="Linear Total" value={nlResult.linear_total?.toFixed(1)} unit="kg CO₂-eq" />
                    <Stat label="Non-Linear Total" value={nlResult.nonlinear_total?.toFixed(1)} unit="kg CO₂-eq" />
                    <Stat
                      label="Deviation"
                      value={`${nlResult.deviation_percent >= 0 ? '+' : ''}${nlResult.deviation_percent?.toFixed(2)}%`}
                      unit={nlResult.converged ? '✅ Converged' : '⚠️ Not converged'}
                    />
                  </div>

                  {/* Per-process comparison table */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm" style={{ color: '#c4c8be' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid #31372a' }}>
                          <th className="text-left py-2 px-3">Process</th>
                          <th className="text-right py-2 px-3">Linear</th>
                          <th className="text-right py-2 px-3">Non-Linear</th>
                          <th className="text-right py-2 px-3">Change</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(nlResult.process_comparison || []).map((p: any, i: number) => (
                          <tr key={i} style={{ borderBottom: '1px solid #272c20' }}>
                            <td className="py-2 px-3">{p.process}</td>
                            <td className="text-right py-2 px-3 font-mono">{p.linear_impact?.toFixed(1)}</td>
                            <td className="text-right py-2 px-3 font-mono">{p.nonlinear_impact?.toFixed(1)}</td>
                            <td className="text-right py-2 px-3 font-mono" style={{
                              color: p.change_percent < 0 ? '#919e65' : '#c66b3d'
                            }}>
                              {p.change_percent >= 0 ? '+' : ''}{p.change_percent?.toFixed(1)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>

                {/* Convergence */}
                {nlResult.convergence_history?.length > 0 && (
                  <Card title="🔄 Iterative Convergence: s_{k+1} = A(s_k)⁻¹ · f">
                    <div className="space-y-1">
                      {nlResult.convergence_history.map((c: any, i: number) => (
                        <div key={i} className="flex justify-between text-sm font-mono"
                          style={{ color: '#c4c8be' }}>
                          <span>Iter {c.iteration}</span>
                          <span>δ = {c.delta?.toExponential(2)}</span>
                          <span>Impact = {c.impact?.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
              </>
            )}
          </div>
        </>
      )}
    </div>
  )
}


// ─── Sub-components ────────────────────────────────────────────────

function KPICard({ label, value, unit, icon }: {
  label: string; value: string; unit: string; icon: string
}) {
  return (
    <div
      className="rounded-2xl p-4 transition-all hover:scale-[1.02]"
      style={{
        background: 'linear-gradient(145deg, #1c2116, #272c20)',
        border: '1px solid #31372a',
      }}
    >
      <div className="text-xl mb-2">{icon}</div>
      <div className="text-xs mb-1" style={{ color: '#8e9289' }}>{label}</div>
      <div className="text-lg font-semibold font-mono" style={{ color: '#e0e5d3' }}>{value}</div>
      <div className="text-xs" style={{ color: '#8e9289' }}>{unit}</div>
    </div>
  )
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      className="rounded-2xl p-6"
      style={{
        background: '#1c2116',
        border: '1px solid #272c20',
      }}
    >
      <h3 className="font-serif text-base mb-4" style={{ color: '#e0e5d3' }}>{title}</h3>
      {children}
    </div>
  )
}

function MatrixDisplay({ label, data }: { label: string; data: number[] }) {
  return (
    <div className="rounded-xl p-3" style={{ background: '#272c20', border: '1px solid #31372a' }}>
      <div className="text-xs mb-2" style={{ color: '#8e9289' }}>{label}</div>
      <div className="font-mono text-sm space-y-0.5">
        {(data || []).map((v, i) => (
          <div key={i} style={{ color: '#bfcd8f' }}>
            [{i}] = {typeof v === 'number' ? v.toFixed(4) : v}
          </div>
        ))}
      </div>
    </div>
  )
}

function Stat({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div className="rounded-xl p-3" style={{ background: '#272c20', border: '1px solid #31372a' }}>
      <div className="text-xs mb-1" style={{ color: '#8e9289' }}>{label}</div>
      <div className="text-base font-mono font-semibold" style={{ color: '#e0e5d3' }}>{value}</div>
      <div className="text-xs" style={{ color: '#8e9289' }}>{unit}</div>
    </div>
  )
}
