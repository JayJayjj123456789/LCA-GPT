import { useState } from 'react'
import { login, register } from '../api'

interface Props {
  onAuthed: (email: string) => void
}

export default function LoginView({ onAuthed }: Props) {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const res = mode === 'login'
        ? await login(email, password)
        : await register(email, password)
      onAuthed(res.email)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{ background: '#10150b' }}>
      <div className="w-full max-w-md">
        {/* Brand */}
        <div className="flex items-center gap-3 justify-center mb-8">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center overflow-hidden shrink-0" style={{ background: '#8b9d83' }}>
            <span className="material-symbols-outlined text-white" style={{ fontSize: 24, fontVariationSettings: "'FILL' 1" }}>eco</span>
          </div>
          <div>
            <h1 className="text-xl font-semibold leading-tight" style={{ fontFamily: 'Literata, Georgia, serif', color: '#b9ccb0' }}>Global Supply Chain</h1>
            <p style={{ color: '#8e9289', fontSize: 13 }}>FY24 Carbon Audit</p>
          </div>
        </div>

        {/* Card */}
        <div className="rounded-2xl p-8" style={{ background: '#1c2116', border: '1px solid #31372a' }}>
          <h2 className="text-lg font-semibold mb-1" style={{ fontFamily: 'Literata, Georgia, serif', color: '#e0e5d3' }}>
            {mode === 'login' ? 'Welcome back' : 'Create your account'}
          </h2>
          <p className="mb-6" style={{ color: '#8e9289', fontSize: 13 }}>
            {mode === 'login'
              ? 'Sign in to access your audits, chat and reports.'
              : 'Each user has their own private audit workspace.'}
          </p>

          <form onSubmit={submit} className="flex flex-col gap-4">
            <div>
              <label className="block mb-1.5" style={{ color: '#8e9289', fontSize: 13, fontWeight: 600 }}>Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@company.com"
                autoComplete="email"
                required
                className="w-full px-3.5 py-2.5 rounded-xl outline-none transition-colors"
                style={{ background: '#10150b', border: '1px solid #31372a', color: '#e0e5d3', fontSize: 14 }}
                onFocus={e => { (e.currentTarget as HTMLElement).style.borderColor = '#8b9d83' }}
                onBlur={e => { (e.currentTarget as HTMLElement).style.borderColor = '#31372a' }}
              />
            </div>
            <div>
              <label className="block mb-1.5" style={{ color: '#8e9289', fontSize: 13, fontWeight: 600 }}>Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder={mode === 'signup' ? 'At least 6 characters' : 'Your password'}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                required
                className="w-full px-3.5 py-2.5 rounded-xl outline-none transition-colors"
                style={{ background: '#10150b', border: '1px solid #31372a', color: '#e0e5d3', fontSize: 14 }}
                onFocus={e => { (e.currentTarget as HTMLElement).style.borderColor = '#8b9d83' }}
                onBlur={e => { (e.currentTarget as HTMLElement).style.borderColor = '#31372a' }}
              />
            </div>

            {error && (
              <div className="text-sm rounded-lg px-3 py-2.5" style={{ background: 'rgba(192,57,43,0.1)', border: '1px solid rgba(192,57,43,0.35)', color: '#f27a6d' }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full py-2.5 rounded-xl font-semibold cursor-pointer transition-opacity hover:opacity-90 disabled:opacity-60"
              style={{ background: '#b9ccb0', color: '#253421', fontSize: 14, letterSpacing: '0.05em' }}
            >
              {busy ? 'Please wait…' : mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 pt-5 text-center" style={{ borderTop: '1px solid rgba(68,72,65,0.4)' }}>
            <span style={{ color: '#8e9289', fontSize: 13 }}>
              {mode === 'login' ? 'New here?' : 'Already have an account?'}
            </span>{' '}
            <button
              onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setError('') }}
              className="cursor-pointer font-semibold underline underline-offset-2"
              style={{ color: '#b9ccb0', fontSize: 13 }}
            >
              {mode === 'login' ? 'Create an account' : 'Sign in'}
            </button>
          </div>
        </div>

        <p className="text-center mt-6" style={{ color: '#8e9289', fontSize: 12 }}>
          Your audits, chat history and reports are private to your account.
        </p>
      </div>
    </div>
  )
}
