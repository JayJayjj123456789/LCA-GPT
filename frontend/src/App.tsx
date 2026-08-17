import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import DashboardView from './views/DashboardView'
import AuditView from './views/AuditView'
import GraphView from './views/GraphView'
import StrategiesView from './views/StrategiesView'
import ReportsView from './views/ReportsView'
import LiveDemoView from './views/LiveDemoView'
import LoginView from './views/LoginView'
import { getAllAudits, getMe, getToken, logout, type AnalysisData } from './api'

export type NavView = 'dashboard' | 'audit' | 'graph' | 'strategies' | 'reports' | 'livedemo'

export default function App() {
  const [user, setUser]     = useState<string | null>(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null)
  const [audits, setAudits]     = useState<AnalysisData[]>([])
  const [graphKey, setGraphKey] = useState(0)
  const [activeView, setActiveView] = useState<NavView>('dashboard')

  // Restore session on load
  useEffect(() => {
    if (!getToken()) { setAuthLoading(false); return }
    getMe()
      .then(setUser)
      .catch(() => { logout() })
      .finally(() => setAuthLoading(false))
  }, [])

  // Load this user's audits whenever they log in / switch account
  useEffect(() => {
    if (!user) return
    getAllAudits()
      .then(loaded => { setAudits(loaded); setAnalysis(loaded[0] ?? null) })
      .catch(() => {})
  }, [user])

  const handleAnalyzed = (data: AnalysisData) => {
    setAnalysis(data)
    setAudits(prev => [data, ...prev])   // prepend newest first
    setGraphKey(k => k + 1)
    setActiveView('dashboard')
  }

  const handleCleared = () => {
    setAnalysis(null)
    setAudits([])
    setGraphKey(k => k + 1)   // force graph remount with fresh data
    setActiveView('dashboard') // navigate to dashboard for real-time state
  }

  const refreshAudits = () => {
    if (!user) return
    getAllAudits()
      .then(loaded => { setAudits(loaded); setAnalysis(loaded[0] ?? null) })
      .catch(() => {})
  }

  const handleLogout = async () => {
    await logout()
    setUser(null)
    setAnalysis(null)
    setAudits([])
    setActiveView('dashboard')
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#10150b' }}>
        <span className="material-symbols-outlined animate-spin" style={{ color: '#8b9d83', fontSize: 32 }}>progress_activity</span>
      </div>
    )
  }

  if (!user) {
    return <LoginView onAuthed={setUser} />
  }

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return <DashboardView analysis={analysis} onNavigate={setActiveView} />
      case 'audit':
        return <AuditView analysis={analysis} graphKey={graphKey} onAnalyzed={handleAnalyzed} />
      case 'graph':
        return <GraphView analysis={analysis} audits={audits} graphKey={graphKey} onNavigate={setActiveView} />
      case 'strategies':
        return <StrategiesView analysis={analysis} />
      case 'reports':
        return <ReportsView audits={audits} onAuditsChanged={refreshAudits} onNavigate={setActiveView} />
      case 'livedemo':
        return <LiveDemoView analysis={analysis} />
    }
  }

  return (
    <div className="flex min-h-screen" style={{ background: '#10150b' }}>
      <Sidebar
        analysis={analysis}
        user={user}
        onLogout={handleLogout}
        onCleared={handleCleared}
        activeView={activeView}
        onNavigate={setActiveView}
      />
      <main
        className="flex-1 md:ml-80 min-h-screen overflow-y-auto"
        style={{ background: '#10150b' }}
      >
        <div key={activeView} className="animate-fade-in">
          {renderView()}
        </div>
      </main>
    </div>
  )
}
