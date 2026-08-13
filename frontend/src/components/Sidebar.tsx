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
  { key: 'livedemo',   label: 'Live Demo',  icon: 'science'    },
]

const FOOTER_NAV = [
  { label: 'Admin Settings', icon: 'admin_panel_settings' },
  { label: 'Documentation',  icon: 'menu_book'            },
]

export default function Sidebar({ analysis, onCleared, activeView, onNavigate }: Props) {
  const [showClearModal, setShowClearModal] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleClear = () => setShowClearModal(true)

  const handleConfirmClear = async () => {
    setShowClearModal(false)
    await clearGraph()
    onCleared()
  }

  const handleExport = async () => {
    if (analysis) await downloadPdfReport(analysis)
  }

  const navContent = (
      <>
      {/* ── Brand Header ── */}
      <div className="flex items-center gap-4 px-2">
        <div className="w-14 h-14 rounded-xl flex items-center justify-center overflow-hidden shrink-0" style={{ background: '#8b9d83' }}>
          <span className="material-symbols-outlined text-white" style={{ fontSize: 30, fontVariationSettings: "'FILL' 1" }}>eco</span>
        </div>
        <div>
          <h1 className="text-xl font-semibold leading-tight" style={{ fontFamily: 'Literata, Georgia, serif', color: '#b9ccb0', maxWidth: 180 }}>Global Supply Chain</h1>
          <p style={{ color: '#8e9289', fontSize: 15 }}>FY24 Carbon Audit</p>
        </div>
      </div>
      {/* ── New Audit CTA ── */}
      <button onClick={() => { onNavigate('audit'); setMobileOpen(false) }}
        className="w-full py-2.5 px-4 rounded-xl font-semibold flex items-center justify-center gap-2 cursor-pointer transition-opacity hover:opacity-90"
        style={{ background: '#b9ccb0', color: '#253421', fontSize: 16, letterSpacing: '0.05em' }}>
        <span className="material-symbols-outlined" style={{ fontSize: 24, fontVariationSettings: "'FILL' 1" }}>add</span>
        New Audit
      </button>
      {/* ── Main Navigation ── */}
      <ul className="flex flex-col gap-1 flex-grow">
        {NAV_ITEMS.map(({ key, label, icon }) => {
          const isActive = activeView === key
          return (
            <li key={key}>
              <button onClick={() => { onNavigate(key); setMobileOpen(false) }}
                className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-base font-medium transition-all cursor-pointer text-left"
                style={{ background: isActive ? 'rgba(139,157,131,0.15)' : 'transparent', color: isActive ? '#b9ccb0' : '#c4c8be', fontWeight: isActive ? 700 : 400, fontSize: 16 }}
                onMouseEnter={e => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'rgba(49,55,42,0.6)' }}
                onMouseLeave={e => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'transparent' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 26, fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0", color: isActive ? '#b9ccb0' : '#8e9289' }}>{icon}</span>
                {label}
              </button>
            </li>
          )
        })}
      </ul>
      {/* ── Footer Actions ── */}
      <div className="flex flex-col gap-2">
        {analysis && (
          <button onClick={handleExport} className="w-full py-2.5 px-4 font-bold rounded-xl cursor-pointer transition-colors flex items-center justify-center gap-2.5"
            style={{ color: '#b9ccb0', border: '1px solid rgba(185,204,176,0.3)', fontSize: 16 }}>
            <span className="material-symbols-outlined" style={{ fontSize: 22 }}>download</span>Export PDF
          </button>
        )}
        <button onClick={handleClear} className="w-full py-2.5 px-4 font-bold rounded-xl cursor-pointer transition-colors flex items-center justify-center gap-2.5"
          style={{ color: '#c0392b', border: '1px solid rgba(192,57,43,0.4)', background: 'rgba(192,57,43,0.08)', fontSize: 16 }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(192,57,43,0.16)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(192,57,43,0.08)' }}>
          <span className="material-symbols-outlined" style={{ fontSize: 22, fontVariationSettings: "'FILL' 1" }}>delete_sweep</span>Clear Data
        </button>
      </div>
      {/* ── Footer Nav ── */}
      <ul className="flex flex-col gap-1 pt-3" style={{ borderTop: '1px solid rgba(68,72,65,0.4)' }}>
        {FOOTER_NAV.map(({ label, icon }) => (
          <li key={label}>
            <a href="#" className="flex items-center gap-3 px-4 py-2 rounded-xl text-base transition-colors" style={{ color: '#8e9289', fontSize: 15 }}
              onMouseEnter={e => ((e.currentTarget as HTMLElement).style.background = 'rgba(49,55,42,0.6)')}
              onMouseLeave={e => ((e.currentTarget as HTMLElement).style.background = 'transparent')}>
              <span className="material-symbols-outlined" style={{ fontSize: 26 }}>{icon}</span>{label}
            </a>
          </li>
        ))}
      </ul>
    </>
  )

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

      {/* ── Mobile hamburger button ── */}
      <button
        className="md:hidden fixed top-4 left-4 z-[60] p-2 rounded-lg"
        style={{ background: '#0b1006', border: '1px solid rgba(68,72,65,0.6)' }}
        onClick={() => setMobileOpen(o => !o)}
        aria-label="Toggle menu"
      >
        <span className="material-symbols-outlined" style={{ color: '#b9ccb0', fontSize: 28 }}>
          {mobileOpen ? 'close' : 'menu'}
        </span>
      </button>

      {/* ── Mobile overlay backdrop ── */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-[55] bg-black/60" onClick={() => setMobileOpen(false)} />
      )}

      {/* ── Mobile drawer ── */}
      <nav
        className={`md:hidden fixed left-0 top-0 h-full w-72 z-[58] flex flex-col p-4 gap-4 border-r overflow-y-auto transition-transform duration-300 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}
        style={{ background: '#0b1006', borderColor: 'rgba(68,72,65,0.4)' }}
      >
        {navContent}
      </nav>

      {/* ── Desktop sidebar ── */}
      <nav
        className="hidden md:flex flex-col h-full p-6 gap-5 fixed left-0 top-0 w-96 z-50 border-r overflow-y-auto"
        style={{ background: '#0b1006', borderColor: 'rgba(68,72,65,0.4)', height: '100vh' }}
      >
        {navContent}
      </nav>
    </>
  )
}
