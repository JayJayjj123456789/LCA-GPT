import { useState } from 'react'
import { clearGraph, downloadPdfReport } from '../api'
import type { AnalysisData } from '../api'
import type { NavView } from '../App'
import ConfirmModal from './ConfirmModal'

interface Props {
  analysis: AnalysisData | null
  onCleared: () => void
  activeView: NavView
  onNavigate: (view: NavView) => void
}

const NAV_ITEMS: { key: NavView; label: string; icon: string }[] = [
  { key: 'dashboard',  label: 'Dashboard',  icon: 'dashboard'  },
  { key: 'audit',      label: 'Audit Tool', icon: 'analytics'  },
  { key: 'graph',      label: 'Graph View', icon: 'hub'        },
  { key: 'strategies', label: 'Strategies', icon: 'psychology' },
  { key: 'reports',    label: 'Reports',    icon: 'assessment' },
]

const FOOTER_NAV = [
  { label: 'Admin Settings', icon: 'admin_panel_settings' },
  { label: 'Documentation',  icon: 'menu_book'            },
]

export default function Sidebar({ analysis, onCleared, activeView, onNavigate }: Props) {
  const [showClearModal, setShowClearModal] = useState(false)

  const handleClear = () => setShowClearModal(true)

  const handleConfirmClear = async () => {
    setShowClearModal(false)
    await clearGraph()
    onCleared()
  }

  const handleExport = async () => {
    if (analysis) await downloadPdfReport(analysis)
  }

  return (
    <>
      <ConfirmModal
        open={showClearModal}
        title="Clear All Data"
        message="This will permanently clear all graph data and reset the session. Any unsaved audit results will be lost."
        confirmLabel="Yes, Clear Data"
        cancelLabel="Cancel"
        danger
        onConfirm={handleConfirmClear}
        onCancel={() => setShowClearModal(false)}
      />
    <nav
      className="hidden md:flex flex-col h-full p-5 gap-7 fixed left-0 top-0 w-80 z-50 border-r"
      style={{
        background: '#0b1006',
        borderColor: 'rgba(68,72,65,0.4)',
        height: '100vh',
      }}
    >
      {/* ── Brand Header ── */}
      <div className="flex items-center gap-4 px-2">
        <div
          className="w-14 h-14 rounded-xl flex items-center justify-center overflow-hidden shrink-0"
          style={{ background: '#8b9d83' }}
        >
          <span
            className="material-symbols-outlined text-white"
            style={{ fontSize: 30, fontVariationSettings: "'FILL' 1" }}
          >
            eco
          </span>
        </div>
        <div>
          <h1
            className="text-xl font-semibold leading-tight"
            style={{ fontFamily: 'Literata, Georgia, serif', color: '#b9ccb0', maxWidth: 180 }}
          >
            Global Supply Chain
          </h1>
          <p style={{ color: '#8e9289', fontSize: 15 }}>FY24 Carbon Audit</p>
        </div>
      </div>

      {/* ── New Audit CTA ── */}
      <button
        onClick={() => onNavigate('audit')}
        className="w-full py-4 px-5 rounded-xl font-semibold flex items-center justify-center gap-2 cursor-pointer transition-opacity hover:opacity-90"
        style={{
          background: '#b9ccb0',
          color: '#253421',
          fontSize: 16,
          letterSpacing: '0.05em',
        }}
      >
        <span className="material-symbols-outlined" style={{ fontSize: 24, fontVariationSettings: "'FILL' 1" }}>add</span>
        New Audit
      </button>

      {/* ── Main Navigation ── */}
      <ul className="flex flex-col gap-1 flex-grow">
        {NAV_ITEMS.map(({ key, label, icon }) => {
          const isActive = activeView === key
          return (
            <li key={key}>
              <button
                onClick={() => onNavigate(key)}
                className="w-full flex items-center gap-3 px-4 py-4 rounded-xl text-base font-medium transition-all cursor-pointer text-left"
                style={{
                  background: isActive ? 'rgba(139,157,131,0.15)' : 'transparent',
                  color: isActive ? '#b9ccb0' : '#c4c8be',
                  fontWeight: isActive ? 700 : 400,
                  fontSize: 16,
                }}
                onMouseEnter={e => {
                  if (!isActive) (e.currentTarget as HTMLElement).style.background = 'rgba(49,55,42,0.6)'
                }}
                onMouseLeave={e => {
                  if (!isActive) (e.currentTarget as HTMLElement).style.background = 'transparent'
                }}
              >
                <span
                  className="material-symbols-outlined"
                  style={{
                    fontSize: 26,
                    fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0",
                    color: isActive ? '#b9ccb0' : '#8e9289',
                  }}
                >
                  {icon}
                </span>
                {label}
              </button>
            </li>
          )
        })}
      </ul>

      {/* ── Footer Actions (export/clear) ── */}
      <div className="flex flex-col gap-2.5">
        {analysis && (
          <button
            onClick={handleExport}
            className="w-full py-4 px-5 font-bold rounded-xl cursor-pointer transition-colors flex items-center justify-center gap-2.5"
            style={{ color: '#b9ccb0', border: '1px solid rgba(185,204,176,0.3)', fontSize: 16 }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 22 }}>download</span>
            Export PDF
          </button>
        )}
        <button
          onClick={handleClear}
          className="w-full py-4 px-5 font-bold rounded-xl cursor-pointer transition-colors flex items-center justify-center gap-2.5"
          style={{ color: '#c0392b', border: '1px solid rgba(192,57,43,0.4)', background: 'rgba(192,57,43,0.08)', fontSize: 16 }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(192,57,43,0.16)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(192,57,43,0.08)' }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 22, fontVariationSettings: "'FILL' 1" }}>delete_sweep</span>
          Clear Data
        </button>
      </div>

      {/* ── Footer Nav ── */}
      <ul
        className="flex flex-col gap-1 pt-4"
        style={{ borderTop: '1px solid rgba(68,72,65,0.4)' }}
      >
        {FOOTER_NAV.map(({ label, icon }) => (
          <li key={label}>
            <a
              href="#"
              className="flex items-center gap-3 px-4 py-3 rounded-xl text-base transition-colors"
              style={{ color: '#8e9289', fontSize: 15 }}
              onMouseEnter={e => ((e.currentTarget as HTMLElement).style.background = 'rgba(49,55,42,0.6)')}
              onMouseLeave={e => ((e.currentTarget as HTMLElement).style.background = 'transparent')}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 26 }}>{icon}</span>
              {label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
    </>
  )
}
