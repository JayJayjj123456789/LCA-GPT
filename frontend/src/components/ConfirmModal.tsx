interface Props {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmModal({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  danger = false,
  onConfirm,
  onCancel,
}: Props) {
  if (!open) return null

  return (
    /* Backdrop */
    <div
      onClick={onCancel}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'rgba(0,0,0,0.6)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        animation: 'fadeIn 0.15s ease',
      }}
    >
      {/* Panel */}
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: '#151c10',
          border: '1px solid rgba(185,204,176,0.18)',
          borderRadius: 20,
          padding: '44px 40px 36px',
          width: 480,
          maxWidth: '92vw',
          boxShadow: '0 32px 80px rgba(0,0,0,0.65)',
          animation: 'slideUp 0.22s cubic-bezier(0.34,1.56,0.64,1)',
        }}
      >
        {/* Icon */}
        <div
          style={{
            width: 68,
            height: 68,
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: danger ? 'rgba(220,80,80,0.14)' : 'rgba(139,157,131,0.14)',
            marginBottom: 24,
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{
              fontSize: 36,
              color: danger ? '#e07070' : '#b9ccb0',
              fontVariationSettings: "'FILL' 1",
            }}
          >
            {danger ? 'warning' : 'help'}
          </span>
        </div>

        {/* Title */}
        <h2
          style={{
            fontFamily: 'Literata, Georgia, serif',
            color: '#dce8d4',
            fontSize: 28,
            fontWeight: 700,
            marginBottom: 14,
            lineHeight: 1.25,
          }}
        >
          {title}
        </h2>

        {/* Message */}
        <p
          style={{
            color: '#9ea39a',
            fontSize: 17,
            lineHeight: 1.65,
            marginBottom: 36,
          }}
        >
          {message}
        </p>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
          <button
            onClick={onCancel}
            style={{
              padding: '12px 28px',
              borderRadius: 12,
              border: '1px solid rgba(68,72,65,0.7)',
              background: 'transparent',
              color: '#9ea39a',
              fontSize: 16,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'background 0.15s',
              fontFamily: 'inherit',
            }}
            onMouseEnter={e => ((e.currentTarget as HTMLElement).style.background = 'rgba(49,55,42,0.55)')}
            onMouseLeave={e => ((e.currentTarget as HTMLElement).style.background = 'transparent')}
          >
            {cancelLabel}
          </button>

          <button
            onClick={onConfirm}
            style={{
              padding: '12px 32px',
              borderRadius: 12,
              border: 'none',
              background: danger ? '#c0392b' : '#8b9d83',
              color: danger ? '#fff' : '#0b1006',
              fontSize: 16,
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'opacity 0.15s',
              fontFamily: 'inherit',
              letterSpacing: '0.02em',
            }}
            onMouseEnter={e => ((e.currentTarget as HTMLElement).style.opacity = '0.85')}
            onMouseLeave={e => ((e.currentTarget as HTMLElement).style.opacity = '1')}
          >
            {confirmLabel}
          </button>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn  { from { opacity:0 } to { opacity:1 } }
        @keyframes slideUp { from { opacity:0; transform:translateY(28px) scale(0.95) } to { opacity:1; transform:translateY(0) scale(1) } }
      `}</style>
    </div>
  )
}
