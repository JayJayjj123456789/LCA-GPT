import { useEffect, useState } from 'react'
import { findSimilarAudits } from '../api'
import type { AnalysisData, AuditResult } from '../api'

interface Props {
  data: AnalysisData
}

export default function PastAudits({ data }: Props) {
  const [audits, setAudits] = useState<AuditResult[]>([])
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState<Set<number>>(new Set())

  useEffect(() => {
    const materials = (data.materials || []).map((m) => m.name)
    if (materials.length === 0) return
    setLoading(true)
    findSimilarAudits(materials)
      .then(setAudits)
      .catch(() => setAudits([]))
      .finally(() => setLoading(false))
  }, [data])

  const toggle = (i: number) =>
    setExpanded((prev) => {
      const next = new Set(prev)
      next.has(i) ? next.delete(i) : next.add(i)
      return next
    })

  if (loading) {
    return (
      <div>
        <SectionTitle icon="history">Similar Past Audits</SectionTitle>
        <div className="card p-5">
          <div className="noise-bg" />
          <div className="relative z-10 flex items-center gap-3 text-sm text-on-surface-variant">
            <svg className="animate-spin w-4 h-4 shrink-0" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Searching knowledge base for similar carbon audits…
          </div>
        </div>
      </div>
    )
  }

  if (audits.length === 0) return null

  return (
    <div>
      <SectionTitle icon="history">Similar Past Audits</SectionTitle>

      <div className="space-y-2 animate-stagger">
        {audits.map((audit, i) => {
          const isOpen = expanded.has(i)
          const matchPct = Math.round(audit.match_score * 100)
          const matchColor =
            matchPct >= 80 ? 'chip-tertiary'
              : matchPct >= 50 ? 'chip-primary'
                : 'chip'

          return (
            <div key={i} className="card overflow-hidden">
              <div className="noise-bg" />

              {/* Accordion Header */}
              <button
                onClick={() => toggle(i)}
                className="relative z-10 w-full p-4 flex items-center justify-between gap-4 hover:bg-surface-variant/20 transition-colors duration-150 cursor-pointer text-left"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-9 h-9 rounded-xl bg-tertiary-container/15 border border-tertiary-container/25 flex items-center justify-center shrink-0">
                    <span
                      className="material-symbols-outlined text-tertiary"
                      style={{ fontSize: 16, fontVariationSettings: "'FILL' 1" }}
                    >
                      folder_open
                    </span>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-on-surface truncate" style={{ fontFamily: 'Literata, serif' }}>
                      {audit.project_name}
                    </p>
                    <p className="text-xs text-on-surface-variant mt-0.5">
                      {audit.materials.length} materials · {audit.total_co2.toFixed(1)} kgCO₂e
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2.5 shrink-0">
                  <span className={`chip ${matchColor}`}>
                    {matchPct}% match
                  </span>
                  <span
                    className="material-symbols-outlined text-on-surface-variant transition-transform duration-200"
                    style={{ fontSize: 20, transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}
                  >
                    expand_more
                  </span>
                </div>
              </button>

              {/* Expanded Detail */}
              {isOpen && (
                <div className="relative z-10 px-5 pb-5 border-t border-surface-container-highest/50 pt-4 space-y-4 animate-fade-in">
                  {/* Summary */}
                  <div className="text-sm leading-relaxed text-on-surface-variant">
                    <span className="text-on-surface-variant/50 text-xs uppercase tracking-wider font-semibold block mb-1.5">
                      Summary
                    </span>
                    {audit.summary}
                  </div>

                  {/* CO₂ total */}
                  <div>
                    <span className="text-on-surface-variant/50 text-xs uppercase tracking-wider font-semibold block mb-1.5">
                      Total CO₂e
                    </span>
                    <span className="text-xl font-bold text-tertiary" style={{ fontFamily: 'Literata, serif' }}>
                      {audit.total_co2.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                    <span className="ml-1.5 text-xs text-on-surface-variant">kgCO₂e</span>
                  </div>

                  {/* Material chips */}
                  <div>
                    <span className="text-on-surface-variant/50 text-xs uppercase tracking-wider font-semibold block mb-2">
                      Materials
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {audit.materials.map((m, j) => (
                        <span key={j} className="chip bg-surface-container text-on-surface-variant border border-surface-container-highest">
                          {m}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function SectionTitle({ icon, children }: { icon?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2.5 mb-5">
      {icon && (
        <span className="material-symbols-outlined text-primary-container" style={{ fontSize: 16 }}>
          {icon}
        </span>
      )}
      <h2 className="text-section-label">{children}</h2>
      <div className="flex-1 h-px bg-surface-container-highest ml-1" />
    </div>
  )
}
