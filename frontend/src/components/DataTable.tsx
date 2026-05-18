import { useState } from 'react'
import type { AnalysisData } from '../api'

interface Props {
  data: AnalysisData
}

type Tab = 'materials' | 'energy' | 'transport'

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: 'materials', label: 'Materials',  icon: 'category'       },
  { key: 'energy',    label: 'Energy',     icon: 'bolt'           },
  { key: 'transport', label: 'Transport',  icon: 'local_shipping' },
]

export default function DataTable({ data }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('materials')

  const tabCounts = {
    materials: data.materials?.length ?? 0,
    energy:    data.energy?.length    ?? 0,
    transport: data.transport?.length ?? 0,
  }

  return (
    <div>
      <SectionTitle icon="table_chart">Audit Inventory</SectionTitle>

      {/* Tab Bar */}
      <div className="flex gap-1 mb-0 px-1">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold uppercase tracking-wider rounded-t-xl transition-all duration-150 cursor-pointer border border-b-0 ${
              activeTab === tab.key
                ? 'bg-surface-container-high text-on-surface border-surface-container-highest'
                : 'bg-transparent text-on-surface-variant border-transparent hover:text-on-surface hover:bg-surface-container/50'
            }`}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 14, fontVariationSettings: activeTab === tab.key ? "'FILL' 1" : "'FILL' 0" }}>
              {tab.icon}
            </span>
            {tab.label}
            {tabCounts[tab.key] > 0 && (
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] leading-none ${
                activeTab === tab.key
                  ? 'bg-primary-container/40 text-primary'
                  : 'bg-surface-container-highest text-on-surface-variant'
              }`}>
                {tabCounts[tab.key]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Table Container */}
      <div className="rounded-xl rounded-tl-none overflow-hidden border border-surface-container-highest bg-surface-container-high relative">
        <div className="noise-bg" />
        <div className="relative z-10">
          {activeTab === 'materials' && <MaterialsTable materials={data.materials} />}
          {activeTab === 'energy'    && <EnergyTable    energy={data.energy}       />}
          {activeTab === 'transport' && <TransportTable transport={data.transport} />}
        </div>
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

/* ── Shared Table Shell ─────────────────────────────────────────────────── */
function TableShell({ headers, children }: { headers: string[]; children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-surface-container-highest">
            {headers.map((h, i) => (
              <th
                key={h}
                className={`p-3 text-section-label text-on-surface-variant/70 font-medium ${
                  i === 0 ? 'text-left' : i === headers.length - 1 ? 'text-left' : 'text-right'
                }`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="animate-stagger">{children}</tbody>
      </table>
    </div>
  )
}

/* ── Source cell: renders URLs as clickable links ────────────────────────── */
function SourceCell({ note }: { note: string }) {
  if (!note) return <span className="text-on-surface-variant/30">—</span>

  // Extract URL from note text (e.g. "Source: ... — https://..." or raw URL)
  const urlMatch = note.match(/https?:\/\/[^\s]+/)
  const url = urlMatch ? urlMatch[0] : null
  // Display text: everything before the URL, or the full note if no URL
  const displayText = url ? note.replace(url, '').replace(/[—\-–]\s*$/, '').trim() : note

  if (url) {
    return (
      <div className="flex flex-col gap-0.5">
        {displayText && <span className="text-on-surface-variant/60 text-xs leading-tight">{displayText}</span>}
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs underline underline-offset-2 decoration-primary/40 hover:decoration-primary text-primary/80 hover:text-primary transition-colors truncate max-w-[220px] inline-block"
          title={url}
        >
          {url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')}
        </a>
      </div>
    )
  }

  return <span className="text-on-surface-variant/60 text-xs">{note}</span>
}

/* ── Row helper ─────────────────────────────────────────────────────────── */
function TR({ cells }: {
  cells: { value: string | number; align?: 'left' | 'right'; className?: string; isSource?: boolean }[]
}) {
  return (
    <tr className="border-b border-surface-container-highest/40 hover:bg-surface-variant/20 transition-colors duration-100 group">
      {cells.map((cell, i) => (
        <td
          key={i}
          className={`p-3 ${cell.align === 'right' ? 'text-right' : 'text-left'} ${cell.className ?? 'text-on-surface-variant'}`}
        >
          {cell.isSource ? <SourceCell note={cell.value as string} /> : cell.value}
        </td>
      ))}
    </tr>
  )
}

/* ── Materials ─────────────────────────────────────────────────────────── */
function MaterialsTable({ materials }: { materials: AnalysisData['materials'] }) {
  if (!materials || materials.length === 0) return <EmptyState />
  return (
    <TableShell headers={['Material', 'Amount', 'Unit', 'EF', 'Subtotal (CO₂e)', 'Source']}>
      {materials.map((m, i) => (
        <TR
          key={i}
          cells={[
            { value: m.name, className: 'text-on-surface font-medium' },
            { value: m.amount.toFixed(2), align: 'right' },
            { value: m.unit },
            { value: m.emission_factor.toFixed(4), align: 'right' },
            { value: (m.amount * m.emission_factor).toFixed(2), align: 'right', className: 'text-tertiary font-semibold tabular-nums' },
            { value: m.note, isSource: true },
          ]}
        />
      ))}
    </TableShell>
  )
}

/* ── Energy ─────────────────────────────────────────────────────────────── */
function EnergyTable({ energy }: { energy: AnalysisData['energy'] }) {
  if (!energy || energy.length === 0) return <EmptyState />
  return (
    <TableShell headers={['Type', 'Usage', 'Unit', 'EF', 'Subtotal (CO₂e)', 'Source']}>
      {energy.map((e, i) => (
        <TR
          key={i}
          cells={[
            { value: e.type, className: 'text-on-surface font-medium' },
            { value: e.usage.toFixed(2), align: 'right' },
            { value: e.unit },
            { value: e.emission_factor.toFixed(4), align: 'right' },
            { value: (e.usage * e.emission_factor).toFixed(2), align: 'right', className: 'text-secondary font-semibold tabular-nums' },
            { value: e.note, isSource: true },
          ]}
        />
      ))}
    </TableShell>
  )
}

/* ── Transport ─────────────────────────────────────────────────────────── */
function TransportTable({ transport }: { transport: AnalysisData['transport'] }) {
  if (!transport || transport.length === 0) return <EmptyState />
  return (
    <TableShell headers={['Method', 'Distance', 'Unit', 'EF', 'Subtotal (CO₂e)', 'Source']}>
      {transport.map((t, i) => (
        <TR
          key={i}
          cells={[
            { value: t.method, className: 'text-on-surface font-medium' },
            { value: t.distance.toFixed(2), align: 'right' },
            { value: t.unit },
            { value: t.emission_factor.toFixed(4), align: 'right' },
            { value: (t.distance * t.emission_factor).toFixed(2), align: 'right', className: 'text-error font-semibold tabular-nums' },
            { value: t.note, isSource: true },
          ]}
        />
      ))}
    </TableShell>
  )
}

function EmptyState() {
  return (
    <div className="py-12 flex flex-col items-center justify-center gap-3 text-center">
      <span className="material-symbols-outlined text-on-surface-variant/30" style={{ fontSize: 32 }}>
        table_rows
      </span>
      <p className="text-sm text-on-surface-variant">No data available for this category</p>
    </div>
  )
}
