interface Props {
  recommendations: string[]
}

const ICONS = ['eco', 'bolt', 'local_shipping', 'factory', 'recycling', 'energy_savings_leaf']

export default function Recommendations({ recommendations }: Props) {
  if (!recommendations || recommendations.length === 0) return null

  return (
    <div>
      <SectionTitle icon="lightbulb">Strategic Insights</SectionTitle>
      <div className="space-y-2.5 animate-stagger">
        {recommendations.map((rec, i) => (
          <div
            key={i}
            className="card-inset p-4 flex items-start gap-3 hover:border-primary/25 transition-colors duration-150 group"
          >
            {/* Icon */}
            <div className="w-8 h-8 rounded-lg bg-primary-container/15 border border-primary-container/20 flex items-center justify-center shrink-0 mt-0.5 group-hover:bg-primary-container/25 transition-colors duration-150">
              <span
                className="material-symbols-outlined text-primary"
                style={{ fontSize: 15, fontVariationSettings: "'FILL' 1" }}
              >
                {ICONS[i % ICONS.length]}
              </span>
            </div>

            {/* Content */}
            <p className="text-sm text-on-surface-variant leading-relaxed group-hover:text-on-surface transition-colors duration-150">
              {rec}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

function SectionTitle({ icon, children }: { icon?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2.5 mb-4">
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
