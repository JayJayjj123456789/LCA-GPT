import type { AnalysisData } from '../api'

interface Props {
  data: AnalysisData
}

export default function Dashboard({ data }: Props) {
  const itemsCount = (data.materials?.length || 0) + (data.energy?.length || 0)
  const score      = data.optimization_score || 0
  const co2        = data.total_estimated_co2 || 0
  const scorePercent = Math.min(score, 100)

  const co2Display = co2 > 1000
    ? `${(co2 / 1000).toFixed(2)}t`
    : `${co2.toFixed(1)}`

  return (
    <div>
      <SectionTitle icon="monitoring">Key Metrics</SectionTitle>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          label="Active Supplier"
          value={data.project_info?.supplier || '—'}
          icon="factory"
          accent="#8b9d83"
          sub="Supply chain tier 1"
          subIcon="account_tree"
          subColor="#8b9d83"
        />
        <MetricCard
          label="Items Tracked"
          value={itemsCount > 0 ? itemsCount.toLocaleString() : '0'}
          icon="inventory_2"
          accent="#bfcd8f"
          sub="Materials + Energy sources"
          subColor="#8e9289"
        />
        <MetricCard
          label="Carbon Footprint"
          value={co2Display}
          unit="kgCO₂e"
          icon="co2"
          accent="#c66b3d"
          sub="Lifecycle total"
          subIcon="warning"
          subColor="#ffb694"
          danger
        />
        <MetricCard
          label="Optimization Score"
          value={score > 0 ? score.toString() : '—'}
          icon="check_circle"
          accent="#919e65"
          sub="Industry benchmark"
          subColor="#bfcd8f"
          progress={scorePercent}
        />
      </div>
    </div>
  )
}

function SectionTitle({ icon, children }: { icon?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 mb-7">
      {icon && (
        <span
          className="material-symbols-outlined"
          style={{ fontSize: 20, color: '#8b9d83', fontVariationSettings: "'FILL' 1" }}
        >
          {icon}
        </span>
      )}
      <h2
        style={{
          fontFamily: 'Plus Jakarta Sans, sans-serif',
          fontSize: 13,
          fontWeight: 700,
          letterSpacing: '0.08em',
          color: '#8e9289',
          textTransform: 'uppercase',
        }}
      >
        {children}
      </h2>
      <div className="flex-1 h-px" style={{ background: 'rgba(68,72,65,0.5)' }} />
    </div>
  )
}

function MetricCard({
  label, value, unit, icon, accent = '#b9ccb0',
  sub, subIcon, subColor = '#8e9289', progress, danger = false,
}: {
  label: string
  value: string
  unit?: string
  icon: string
  accent?: string
  sub?: string
  subIcon?: string
  subColor?: string
  progress?: number
  danger?: boolean
}) {
  return (
    <div
      className="relative flex flex-col gap-4 overflow-hidden"
      style={{
        background: '#1c2116',
        border: `1px solid ${danger ? 'rgba(198,107,61,0.25)' : 'rgba(68,72,65,0.5)'}`,
        borderRadius: 20,
        padding: '24px 24px 20px',
        height: 200,
        transition: 'border-color 0.2s, box-shadow 0.2s',
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLElement).style.borderColor = accent + '55'
        ;(e.currentTarget as HTMLElement).style.boxShadow = `0 0 0 1px ${accent}22`
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLElement).style.borderColor = danger ? 'rgba(198,107,61,0.25)' : 'rgba(68,72,65,0.5)'
        ;(e.currentTarget as HTMLElement).style.boxShadow = 'none'
      }}
    >
      {/* Noise texture */}
      <div className="noise-bg" />

      {/* Accent top-bar */}
      <div
        style={{
          position: 'absolute',
          top: 0, left: 0, right: 0,
          height: 2,
          background: `linear-gradient(90deg, ${accent}99, ${accent}11)`,
          borderRadius: '20px 20px 0 0',
        }}
      />

      {/* Label + icon row */}
      <div className="relative z-10 flex items-start justify-between">
        <span
          style={{
            fontFamily: 'Plus Jakarta Sans, sans-serif',
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: '0.06em',
            color: '#8e9289',
            textTransform: 'uppercase',
          }}
        >
          {label}
        </span>
        <div
          style={{
            width: 38,
            height: 38,
            borderRadius: 12,
            background: `${accent}18`,
            border: `1px solid ${accent}33`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{ fontSize: 20, color: accent, fontVariationSettings: "'FILL' 1" }}
          >
            {icon}
          </span>
        </div>
      </div>

      {/* Primary value */}
      <div className="relative z-10 flex-1 flex items-end">
        <div>
          <span
            style={{
              fontFamily: 'Literata, Georgia, serif',
              fontSize: 40,
              fontWeight: 700,
              letterSpacing: '-0.02em',
              color: '#e0e5d3',
              lineHeight: 1,
            }}
          >
            {value}
          </span>
          {unit && (
            <span
              style={{
                marginLeft: 6,
                fontSize: 13,
                color: '#8e9289',
                fontFamily: 'Plus Jakarta Sans, sans-serif',
                verticalAlign: 'middle',
              }}
            >
              {unit}
            </span>
          )}
        </div>
      </div>

      {/* Sub-metric */}
      {sub && (
        <div
          className="relative z-10 flex items-center gap-1.5"
          style={{ fontSize: 13, color: subColor, fontFamily: 'Plus Jakarta Sans, sans-serif' }}
        >
          {subIcon && (
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
              {subIcon}
            </span>
          )}
          {sub}
        </div>
      )}

      {/* Progress bar */}
      {progress !== undefined && (
        <div className="relative z-10">
          <div
            style={{
              height: 4,
              background: 'rgba(68,72,65,0.5)',
              borderRadius: 99,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${progress}%`,
                height: '100%',
                background: `linear-gradient(90deg, #52634c, ${accent})`,
                borderRadius: 99,
                transition: 'width 1s cubic-bezier(0.4,0,0.2,1)',
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
