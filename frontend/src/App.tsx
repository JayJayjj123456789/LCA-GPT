import { useState } from 'react'
import Sidebar from './components/Sidebar'
import DashboardView from './views/DashboardView'
import AuditView from './views/AuditView'
import GraphView from './views/GraphView'
import StrategiesView from './views/StrategiesView'
import ReportsView from './views/ReportsView'
import LiveDemoView from './views/LiveDemoView'
import type { AnalysisData } from './api'

export type NavView = 'dashboard' | 'audit' | 'graph' | 'strategies' | 'reports' | 'livedemo'

export default function App() {
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null)
  const [audits, setAudits]     = useState<AnalysisData[]>([])
  const [graphKey, setGraphKey] = useState(0)
  const [activeView, setActiveView] = useState<NavView>('dashboard')

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

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return <DashboardView analysis={analysis} onNavigate={setActiveView} />
      case 'audit':
        return <AuditView analysis={analysis} graphKey={graphKey} onAnalyzed={handleAnalyzed} />
      case 'graph':
        return <GraphView analysis={analysis} graphKey={graphKey} onNavigate={setActiveView} />
      case 'strategies':
        return <StrategiesView analysis={analysis} />
      case 'reports':
        return <ReportsView audits={audits} onNavigate={setActiveView} />
      case 'livedemo':
        return <LiveDemoView analysis={analysis} />
    }
  }

  return (
    <div className="flex min-h-screen" style={{ background: '#10150b' }}>
      <Sidebar
        analysis={analysis}
        onCleared={handleCleared}
        activeView={activeView}
        onNavigate={setActiveView}
      />
      <main
        className="flex-1 md:ml-96 min-h-screen overflow-y-auto"
        style={{ background: '#10150b' }}
      >
        <div key={activeView} className="animate-fade-in">
          {renderView()}
        </div>
      </main>
    </div>
  )
}
