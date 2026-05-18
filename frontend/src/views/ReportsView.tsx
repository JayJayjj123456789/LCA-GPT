import { useState } from 'react'
import type { NavView } from '../App'
import type { AnalysisData } from '../api'

interface Props {
  audits: AnalysisData[]
  onNavigate: (v: NavView) => void
}

const SC_COLORS = ['#b9ccb0', '#bfcd8f', '#ffb694']

function formatCo2(val: number) {
  if (val >= 1000) return `${(val / 1000).toFixed(2)}t`
  return `${val.toFixed(1)}`
}

function getDate() {
  return new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function ReportsView({ audits, onNavigate }: Props) {
  const [sel, setSel] = useState(0)

  if (audits.length === 0) {
    return (
      <div className="px-14 py-12 w-full flex flex-col gap-8">
        <div>
          <h1 className="text-display-lg"
            style={{ fontFamily: 'Literata, serif', color: '#e0e5d3' }}>
            Past Audits &amp; Reports
          </h1>
          <p className="mt-2 text-lg" style={{ color: '#c4c8be' }}>
            Access, review, and export historical carbon footprint analyses.
          </p>
        </div>
        <div className="flex flex-col items-center justify-center min-h-[50vh] gap-6">
          <div className="w-20 h-20 rounded-full flex items-center justify-center"
            style={{ background: 'rgba(185,204,176,0.1)', border: '1px solid rgba(185,204,176,0.2)' }}>
            <span className="material-symbols-outlined" style={{ fontSize: 40, color: '#8b9d83' }}>assessment</span>
          </div>
          <div className="text-center">
            <h2 className="text-2xl font-semibold mb-2"
              style={{ fontFamily: 'Literata, serif', color: '#e0e5d3' }}>No Audit History</h2>
            <p className="text-base" style={{ color: '#8e9289' }}>
              Complete a carbon audit to see reports here.
            </p>
          </div>
          <button onClick={() => onNavigate('audit')}
            className="px-8 py-3 rounded-xl text-sm font-semibold cursor-pointer hover:opacity-90"
            style={{ background: '#b9ccb0', color: '#253421' }}>
            Start Audit
          </button>
        </div>
      </div>
    )
  }

  const selected = audits[sel]
  const co2 = selected.total_estimated_co2 || 0
  const score = selected.optimization_score || 0
  const matCount = selected.materials?.length || 0
  const energyCount = selected.energy?.length || 0

  // Build scope breakdown from materials/energy/transport
  const matCo2 = selected.materials?.reduce((s, m) => s + (m.amount * m.emission_factor), 0) || 0
  const energyCo2 = selected.energy?.reduce((s, e) => s + (e.usage * e.emission_factor), 0) || 0
  const transCo2 = selected.transport?.reduce((s, t) => s + (t.distance * t.emission_factor), 0) || 0
  const total = matCo2 + energyCo2 + transCo2 || co2 || 1

  const scopes = [
    { name: 'Materials', val: matCo2, pct: Math.round((matCo2 / total) * 100), color: SC_COLORS[0] },
    { name: 'Energy',    val: energyCo2, pct: Math.round((energyCo2 / total) * 100), color: SC_COLORS[1] },
    { name: 'Transport', val: transCo2, pct: Math.round((transCo2 / total) * 100), color: SC_COLORS[2] },
  ].filter(s => s.val > 0 || s.pct > 0)

  return (
    <div className="px-14 py-12 w-full flex flex-col gap-8" style={{ height: '100vh', overflow: 'hidden' }}>

      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 shrink-0">
        <div>
          <h1 className="text-display-lg"
            style={{ fontFamily: 'Literata, serif', color: '#e0e5d3' }}>
            Past Audits &amp; Reports
          </h1>
          <p className="mt-2 text-lg" style={{ color: '#c4c8be' }}>
            Access, review, and export historical carbon footprint analyses.
          </p>
        </div>
        <span className="text-sm px-3 py-1 rounded-full"
          style={{ background: '#1c2116', color: '#8e9289', border: '1px solid #444841' }}>
          {audits.length} Audit{audits.length !== 1 ? 's' : ''} Total
        </span>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 flex-1 min-h-0">

        {/* Left: Audit List */}
        <div className="xl:col-span-5 flex flex-col overflow-hidden rounded-xl"
          style={{ background: '#1c2116', border: '1px solid rgba(68,72,65,0.4)' }}>
          <div className="p-4 flex justify-between items-center shrink-0"
            style={{ borderBottom: '1px solid rgba(68,72,65,0.4)', background: '#181d12' }}>
            <h2 className="text-2xl font-medium"
              style={{ fontFamily: 'Literata, serif', color: '#e0e5d3' }}>Recent Audits</h2>
            <span className="text-sm" style={{ color: '#8e9289' }}>{audits.length} Total</span>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-2">
            {audits.map((a, i) => {
              const isActive = sel === i
              return (
                <div key={i} onClick={() => setSel(i)}
                  className="p-4 rounded-lg cursor-pointer relative"
                  style={{
                    background: isActive ? 'rgba(185,204,176,0.06)' : 'rgba(16,21,11,0.5)',
                    border: isActive ? '1px solid rgba(185,204,176,0.35)' : '1px solid transparent',
                  }}>
                  {isActive && <div className="absolute left-0 top-0 bottom-0 w-1 rounded-l-lg" style={{ background: '#b9ccb0' }} />}
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-base font-semibold pr-2"
                      style={{ color: isActive ? '#b9ccb0' : '#e0e5d3' }}>
                      {a.project_info?.name || `Audit #${audits.length - i}`}
                    </h3>
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium shrink-0"
                      style={{ background: '#8b9d83', color: '#101f0d' }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 12 }}>check_circle</span>
                      Verified
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-wider" style={{ color: '#8e9289' }}>Supplier</p>
                      <p className="text-sm mt-0.5" style={{ color: '#c4c8be' }}>
                        {a.project_info?.supplier || '—'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs uppercase tracking-wider" style={{ color: '#8e9289' }}>Total Emissions</p>
                      <p className="text-base font-semibold mt-0.5" style={{ color: '#e0e5d3' }}>
                        {formatCo2(a.total_estimated_co2 || 0)} kgCO₂e
                      </p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right: Detail */}
        <div className="xl:col-span-7 flex flex-col gap-4 overflow-hidden rounded-xl p-6"
          style={{ background: '#1c2116', border: '1px solid rgba(68,72,65,0.4)' }}>

          {/* Detail header */}
          <div className="flex justify-between items-start pb-4 shrink-0"
            style={{ borderBottom: '1px solid rgba(68,72,65,0.3)' }}>
            <div>
              <div className="flex items-center gap-3 mb-1 flex-wrap">
                <h2 className="text-[28px] font-semibold leading-tight"
                  style={{ fontFamily: 'Literata, serif', color: '#e0e5d3' }}>
                  {selected.project_info?.name || 'Untitled Audit'}
                </h2>
                <span className="px-3 py-1 rounded-full text-xs font-medium"
                  style={{ background: '#8b9d83', color: '#101f0d' }}>Verified</span>
              </div>
              <p className="text-sm" style={{ color: '#8e9289' }}>
                Supplier: {selected.project_info?.supplier || '—'} • {getDate()}
              </p>
            </div>
            <div className="flex gap-2 shrink-0">
              {(['picture_as_pdf:Export PDF', 'table_chart:Export CSV'] as const).map(s => {
                const [icon, label] = s.split(':')
                return (
                  <button key={label}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold cursor-pointer"
                    style={{ border: '1px solid #444841', color: '#e0e5d3' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>{icon}</span>
                    {label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Scrollable content */}
          <div className="flex-1 overflow-y-auto space-y-6 pr-1">

            {/* Key metrics */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { icon: 'co2',           label: 'Total Emissions', value: formatCo2(co2),         unit: 'kgCO₂e', color: '#e0e5d3' },
                { icon: 'inventory_2',   label: 'Items Tracked',   value: `${matCount + energyCount}`, unit: 'items',  color: '#b9ccb0' },
                { icon: 'check_circle',  label: 'Opt. Score',      value: score > 0 ? `${score}` : '—', unit: '/100', color: '#bfcd8f' },
              ].map(m => (
                <div key={m.label} className="p-4 rounded-lg"
                  style={{ background: '#181d12', border: '1px solid rgba(68,72,65,0.2)' }}>
                  <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider mb-2"
                    style={{ color: '#8e9289' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 14 }}>{m.icon}</span>
                    {m.label}
                  </div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-[28px] font-semibold"
                      style={{ fontFamily: 'Literata, serif', color: m.color }}>{m.value}</span>
                    <span className="text-xs" style={{ color: '#8e9289' }}>{m.unit}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Scope Breakdown */}
            {scopes.length > 0 && (
              <div>
                <h3 className="text-xl font-medium mb-3 flex items-center gap-2"
                  style={{ fontFamily: 'Literata, serif', color: '#e0e5d3' }}>
                  <span className="material-symbols-outlined" style={{ color: '#b9ccb0', fontSize: 20 }}>pie_chart</span>
                  Emissions Breakdown
                </h3>
                <div className="rounded-lg overflow-hidden"
                  style={{ background: '#0b1006', border: '1px solid rgba(68,72,65,0.25)' }}>
                  <table className="w-full text-sm">
                    <thead>
                      <tr style={{ background: '#181d12', borderBottom: '1px solid rgba(68,72,65,0.25)' }}>
                        {['Category', 'Emissions (kgCO₂e)', 'Share'].map((h, i) => (
                          <th key={h} className="p-3 text-xs font-semibold uppercase tracking-wider"
                            style={{ color: '#8e9289', textAlign: i === 1 ? 'right' : 'left' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {scopes.map(s => (
                        <tr key={s.name} style={{ borderBottom: '1px solid rgba(68,72,65,0.15)' }}>
                          <td className="p-3">
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 rounded-full" style={{ background: s.color }} />
                              <span style={{ color: '#e0e5d3' }}>{s.name}</span>
                            </div>
                          </td>
                          <td className="p-3 text-right font-semibold" style={{ color: '#e0e5d3' }}>
                            {s.val.toFixed(2)}
                          </td>
                          <td className="p-3 w-1/3">
                            <div className="w-full rounded-full h-2 overflow-hidden" style={{ background: '#31372a' }}>
                              <div className="h-full rounded-full" style={{ width: `${s.pct}%`, background: s.color }} />
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Summary */}
            {selected.summary && (
              <div className="p-5 rounded-lg" style={{ background: '#181d12', border: '1px solid rgba(68,72,65,0.2)' }}>
                <h4 className="text-base font-semibold mb-2 flex items-center gap-2" style={{ color: '#e0e5d3' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 16, color: '#b9ccb0' }}>summarize</span>
                  AI Summary
                </h4>
                <p className="text-sm leading-relaxed" style={{ color: '#c4c8be' }}>{selected.summary}</p>
              </div>
            )}

            {/* Recommendations */}
            {selected.recommendations?.length > 0 && (
              <div>
                <h3 className="text-xl font-medium mb-3 flex items-center gap-2"
                  style={{ fontFamily: 'Literata, serif', color: '#e0e5d3' }}>
                  <span className="material-symbols-outlined" style={{ color: '#b9ccb0', fontSize: 20 }}>lightbulb</span>
                  Recommendations
                </h3>
                <div className="flex flex-col gap-2">
                  {selected.recommendations.map((rec, i) => (
                    <div key={i} className="p-4 rounded-lg flex items-start gap-3"
                      style={{ background: '#181d12', border: '1px solid rgba(68,72,65,0.2)' }}>
                      <span className="text-sm font-bold shrink-0 mt-0.5"
                        style={{ color: '#8e9289' }}>{i + 1}.</span>
                      <p className="text-sm leading-relaxed" style={{ color: '#c4c8be' }}>{rec}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
