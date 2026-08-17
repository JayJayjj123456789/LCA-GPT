import { useState, useRef, useEffect } from 'react'
import type { AnalysisData } from '../api'
import { sendChatMessage } from '../api'

interface Props { analysis: AnalysisData | null }
interface Msg  { role: 'ai' | 'user'; text: string }

const INIT: Msg[] = [
  { role: 'ai', text: "I'm your AI Strategy Consultant. Upload a carbon audit PDF to get personalized mitigation strategies and recommendations." },
]

export default function StrategiesView({ analysis }: Props) {
  const [messages, setMessages] = useState<Msg[]>(INIT)
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  // When analysis first loads, add a contextual AI greeting
  useEffect(() => {
    if (analysis) {
      const co2 = analysis.total_estimated_co2 || 0
      const score = analysis.optimization_score || 0
      const name = analysis.project_info?.name || 'your supply chain'
      setMessages([{
        role: 'ai',
        text: `I've analyzed **${name}**. Total estimated carbon footprint: **${co2.toFixed(1)} kgCO₂e** with an optimization score of **${score}/100**. I've identified ${analysis.recommendations?.length || 0} mitigation strategies. Which would you like to explore first?`
      }])
    }
  }, [analysis?.project_info?.name])

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setMessages(m => [...m, { role: 'user', text }])
    setLoading(true)
    try {
      const reply = await sendChatMessage(text)
      setMessages(m => [...m, { role: 'ai', text: reply }])
    } catch {
      setMessages(m => [...m, { role: 'ai', text: 'Sorry, there was an error connecting to the AI. Please ensure the backend is running.' }])
    } finally {
      setLoading(false)
    }
  }

  // Real recommendations from analysis
  const recommendations = analysis?.recommendations || []

  return (
    <div className="px-14 py-12 w-full flex flex-col gap-6" style={{ height: '100vh', overflow: 'hidden' }}>

      {/* Header */}
      <div className="flex justify-between items-end pb-6 shrink-0"
        style={{ borderBottom: '1px solid #181d12' }}>
        <div>
          <h1 className="text-display-lg"
            style={{ fontFamily: 'Literata, serif', color: '#e0e5d3' }}>
            Strategic Insights
          </h1>
          <p className="mt-1 text-lg" style={{ color: '#c4c8be' }}>
            AI-driven recommendations for carbon flow optimization and mitigation.
          </p>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">

        {/* Chat panel */}
        <section className="lg:col-span-5 flex flex-col rounded-xl overflow-hidden relative h-full"
          style={{ background: '#1c2116', border: '1px solid rgba(68,72,65,0.3)' }}>
          <div className="noise-bg" />
          <div className="relative z-10 flex items-center gap-3 p-4"
            style={{ background: '#272c20', borderBottom: '1px solid rgba(68,72,65,0.3)' }}>
            <div className="p-2 rounded-full" style={{ background: 'rgba(185,204,176,0.2)' }}>
              <span className="material-symbols-outlined"
                style={{ color: '#b9ccb0', fontSize: 19, fontVariationSettings: "'FILL' 1" }}>
                psychology
              </span>
            </div>
            <div>
              <h2 className="text-xl font-medium"
                style={{ fontFamily: 'Literata, serif', color: '#e0e5d3' }}>
                AI Strategy Consultant
              </h2>
              <p className="text-xs" style={{ color: '#8e9289' }}>
                {analysis ? `Analyzing: ${analysis.project_info?.name || 'Current Audit'}` : 'Awaiting audit data'}
              </p>
            </div>
          </div>

          {/* Messages */}
          <div className="relative z-10 flex-1 overflow-y-auto p-4 flex flex-col gap-4">
            {messages.map((m, i) => (
              m.role === 'ai' ? (
                <div key={i} className="flex gap-3 max-w-[85%]">
                  <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center mt-1"
                    style={{ background: 'rgba(185,204,176,0.2)' }}>
                    <span className="material-symbols-outlined" style={{ color: '#b9ccb0', fontSize: 16 }}>psychology</span>
                  </div>
                  <div className="p-3 rounded-lg rounded-tl-none text-sm leading-relaxed"
                    style={{ background: '#272c20', border: '1px solid rgba(68,72,65,0.3)', color: '#e0e5d3' }}>
                    {m.text}
                  </div>
                </div>
              ) : (
                <div key={i} className="flex gap-3 max-w-[85%] self-end flex-row-reverse">
                  <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center mt-1 text-sm font-bold"
                    style={{ background: '#8b9d83', color: '#101f0d' }}>U</div>
                  <div className="p-3 rounded-lg rounded-tr-none text-sm leading-relaxed"
                    style={{ background: '#8b9d83', color: '#253421' }}>
                    {m.text}
                  </div>
                </div>
              )
            ))}
            {loading && (
              <div className="flex gap-3 max-w-[85%]">
                <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center"
                  style={{ background: 'rgba(185,204,176,0.2)' }}>
                  <span className="material-symbols-outlined" style={{ color: '#b9ccb0', fontSize: 16 }}>psychology</span>
                </div>
                <div className="p-3 rounded-lg rounded-tl-none flex items-center gap-1"
                  style={{ background: '#272c20', border: '1px solid rgba(68,72,65,0.3)' }}>
                  {[0, 1, 2].map(d => (
                    <div key={d} className="w-1.5 h-1.5 rounded-full animate-bounce"
                      style={{ background: '#8e9289', animationDelay: `${d * 150}ms` }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* Input */}
          <div className="relative z-10 p-4"
            style={{ background: '#181d12', borderTop: '1px solid rgba(68,72,65,0.3)' }}>
            <div className="relative">
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && send()}
                className="w-full rounded-lg pl-4 pr-12 py-3 text-sm outline-none"
                style={{ background: '#10150b', border: '1px solid rgba(68,72,65,0.6)', color: '#e0e5d3' }}
                placeholder={analysis ? 'Ask about mitigation strategies...' : 'Upload an audit first to get personalized insights...'}
              />
              <button onClick={send}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 cursor-pointer"
                style={{ color: '#b9ccb0' }}>
                <span className="material-symbols-outlined"
                  style={{ fontSize: 20, fontVariationSettings: "'FILL' 1" }}>send</span>
              </button>
            </div>
          </div>
        </section>

        {/* Right column */}
        <section className="lg:col-span-7 flex flex-col gap-6 overflow-y-auto min-h-0">

          {/* Recommendations from real analysis */}
          {recommendations.length > 0 ? (
            <div className="rounded-xl p-6 relative overflow-hidden flex flex-col gap-4"
              style={{ background: '#1c2116', border: '1px solid rgba(68,72,65,0.3)' }}>
              <div className="noise-bg" />
              <div className="relative z-10">
                <h3 className="text-[28px] font-semibold mb-4 flex items-center gap-2"
                  style={{ fontFamily: 'Literata, serif', color: '#e0e5d3' }}>
                  <span className="material-symbols-outlined" style={{ color: '#b9ccb0', fontSize: 22 }}>lightbulb</span>
                  AI Recommendations
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {recommendations.map((rec, i) => {
                    const colors = [
                      { border: 'rgba(185,204,176,0.4)', scope: 'rgba(185,204,176,0.15)', scopeText: '#b9ccb0', scopeBorder: 'rgba(185,204,176,0.3)', label: 'Scope 2' },
                      { border: 'rgba(255,182,148,0.4)', scope: 'rgba(255,182,148,0.15)', scopeText: '#ffb694', scopeBorder: 'rgba(255,182,148,0.3)', label: 'Scope 3' },
                      { border: 'rgba(191,205,143,0.4)', scope: 'rgba(191,205,143,0.15)', scopeText: '#bfcd8f', scopeBorder: 'rgba(191,205,143,0.3)', label: 'Scope 1' },
                    ]
                    const c = colors[i % colors.length]
                    return (
                      <div key={i}
                        className="rounded-xl p-5 relative overflow-hidden flex flex-col cursor-pointer transition-all"
                        style={{ background: '#181d12', border: `1px solid rgba(68,72,65,0.3)` }}
                        onMouseEnter={e => ((e.currentTarget as HTMLElement).style.borderColor = c.border)}
                        onMouseLeave={e => ((e.currentTarget as HTMLElement).style.borderColor = 'rgba(68,72,65,0.3)')}
                      >
                        <div className="flex justify-between items-start mb-3">
                          <span className="px-2 py-1 rounded text-xs font-semibold"
                            style={{ background: c.scope, color: c.scopeText, border: `1px solid ${c.scopeBorder}` }}>
                            {c.label}
                          </span>
                          <span className="text-xs font-semibold" style={{ color: '#8e9289' }}>#{i + 1}</span>
                        </div>
                        <p className="text-sm leading-relaxed flex-grow" style={{ color: '#c4c8be' }}>{rec}</p>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          ) : (
            /* Empty state when no analysis */
            <div className="rounded-xl p-12 flex flex-col items-center gap-4 text-center"
              style={{ background: '#1c2116', border: '1px solid rgba(68,72,65,0.3)' }}>
              <div className="noise-bg" />
              <span className="material-symbols-outlined relative z-10"
                style={{ fontSize: 48, color: '#31372a' }}>psychology</span>
              <div className="relative z-10">
                <h3 className="text-xl font-semibold mb-2"
                  style={{ fontFamily: 'Literata, serif', color: '#e0e5d3' }}>
                  No Strategies Yet
                </h3>
                <p className="text-base" style={{ color: '#8e9289' }}>
                  Run a carbon audit to generate AI-powered mitigation strategies tailored to your supply chain.
                </p>
              </div>
            </div>
          )}

          {/* Analysis summary card */}
          {analysis && (
            <div className="rounded-xl p-6 relative overflow-hidden"
              style={{ background: '#1c2116', border: '1px solid rgba(68,72,65,0.3)' }}>
              <div className="noise-bg" />
              <div className="relative z-10">
                <h3 className="text-xl font-semibold mb-3 flex items-center gap-2"
                  style={{ fontFamily: 'Literata, serif', color: '#e0e5d3' }}>
                  <span className="material-symbols-outlined" style={{ color: '#bfcd8f', fontSize: 20 }}>summarize</span>
                  AI Analysis Summary
                </h3>
                <p className="text-base leading-relaxed" style={{ color: '#c4c8be' }}>
                  {analysis.summary || 'No summary generated.'}
                </p>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
