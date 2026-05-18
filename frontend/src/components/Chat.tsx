import { useState, useRef, useEffect } from 'react'
import { sendChatMessage } from '../api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const QUICK_QUESTIONS = [
  'What are the top carbon hotspots?',
  'How can I reduce CO₂ by 20%?',
  'Explain my Scope 3 emissions',
  'Suggest green material swaps',
]

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (question?: string) => {
    const q = (question ?? input).trim()
    if (!q || loading) return
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: q }])
    setLoading(true)
    try {
      const answer = await sendChatMessage(q)
      setMessages((prev) => [...prev, { role: 'assistant', content: answer }])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I could not process your question right now. Please try again.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <SectionTitle icon="psychology">AI Strategy Consultant</SectionTitle>

      <div className="card overflow-hidden">
        <div className="noise-bg" />

        {/* Message Area */}
        <div className="relative z-10 h-72 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            /* Empty State */
            <div className="h-full flex flex-col items-center justify-center text-center space-y-4 animate-fade-in">
              <div className="w-14 h-14 rounded-2xl bg-primary-container/15 border border-primary-container/25 flex items-center justify-center">
                <span
                  className="material-symbols-outlined text-primary"
                  style={{ fontSize: 26, fontVariationSettings: "'FILL' 1" }}
                >
                  psychology
                </span>
              </div>
              <div>
                <p className="text-sm font-semibold text-on-surface mb-1" style={{ fontFamily: 'Literata, serif' }}>
                  AI Carbon Strategy Consultant
                </p>
                <p className="text-xs text-on-surface-variant/60 max-w-[300px] leading-relaxed">
                  Ask about LCA methodologies, emission factors, carbon reduction strategies, or your uploaded audit data.
                </p>
              </div>
              <div className="flex flex-wrap gap-2 justify-center mt-1">
                {QUICK_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="text-xs px-3 py-1.5 rounded-full bg-surface-container border border-surface-container-highest text-on-surface-variant hover:text-primary hover:border-primary/30 hover:bg-primary/8 transition-all duration-150 cursor-pointer"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Messages */
            messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-2.5 animate-fade-in ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-xl bg-primary-container/15 border border-primary-container/20 flex items-center justify-center shrink-0 mt-0.5">
                    <span
                      className="material-symbols-outlined text-primary"
                      style={{ fontSize: 14, fontVariationSettings: "'FILL' 1" }}
                    >
                      psychology
                    </span>
                  </div>
                )}
                <div
                  className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-primary-container text-on-primary-container rounded-br-sm ml-8'
                      : 'bg-surface-container border border-surface-container-low text-on-surface rounded-bl-sm'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))
          )}

          {/* Typing Indicator */}
          {loading && (
            <div className="flex gap-2.5 animate-fade-in">
              <div className="w-7 h-7 rounded-xl bg-primary-container/15 border border-primary-container/20 flex items-center justify-center shrink-0 mt-0.5">
                <span className="material-symbols-outlined text-primary" style={{ fontSize: 14, fontVariationSettings: "'FILL' 1" }}>
                  psychology
                </span>
              </div>
              <div className="bg-surface-container border border-surface-container-low rounded-2xl rounded-bl-sm px-4 py-3">
                <span className="flex gap-1 items-center h-4">
                  {[0, 150, 300].map((delay) => (
                    <span
                      key={delay}
                      className="w-1.5 h-1.5 rounded-full bg-on-surface-variant/40 animate-bounce"
                      style={{ animationDelay: `${delay}ms` }}
                    />
                  ))}
                </span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input Bar */}
        <div className="relative z-10 border-t border-surface-container-highest p-3 flex gap-2 items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask about emissions, EF data, or reduction strategies…"
            className="flex-1 bg-surface-container border border-surface-container-low rounded-xl px-4 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/35 focus:outline-none focus:border-primary/40 focus:bg-surface-container-high transition-all duration-150"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className="px-4 py-2.5 bg-primary-container text-on-primary-container rounded-xl text-xs font-semibold uppercase tracking-widest hover:bg-primary hover:text-on-primary disabled:opacity-25 disabled:cursor-not-allowed transition-all duration-150 cursor-pointer active:scale-95 shrink-0"
          >
            Send
          </button>
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
