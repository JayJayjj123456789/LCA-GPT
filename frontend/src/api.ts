import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

export interface AnalysisData {
  project_info: {
    name: string
    supplier: string
  }
  materials: { name: string; amount: number; unit: string; emission_factor: number; note: string }[]
  energy: { type: string; usage: number; unit: string; emission_factor: number; note: string }[]
  transport: { method: string; distance: number; unit: string; emission_factor: number; note: string }[]
  total_estimated_co2: number
  optimization_score: number
  recommendations: string[]
  summary: string
}

export interface GraphData {
  nodes: { id: string; label: string; size: number; color: string }[]
  edges: { source: string; target: string; label: string }[]
}

export interface ChartData {
  data: any[]
  layout: any
}

export interface AuditResult {
  project_name: string
  summary: string
  total_co2: number
  materials: string[]
  match_score: number
}

export const analyzePdf = async (file: File): Promise<AnalysisData> => {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<AnalysisData>('/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export const getGraph = async (): Promise<GraphData> => {
  const { data } = await api.get<GraphData>('/graph')
  return data
}

export const clearGraph = async (): Promise<void> => {
  await api.delete('/graph')
}

export const getHotspotChart = async (materials: any[], signal?: AbortSignal): Promise<ChartData> => {
  const { data } = await api.post<ChartData>('/charts/hotspot', { materials }, { signal, timeout: 30000 })
  return data
}

export const getPieChart = async (analysisData: AnalysisData, signal?: AbortSignal): Promise<ChartData> => {
  const { data } = await api.post<ChartData>('/charts/pie', analysisData, { signal, timeout: 30000 })
  return data
}

export const getSankeyChart = async (analysisData: AnalysisData, signal?: AbortSignal): Promise<ChartData> => {
  const { data } = await api.post<ChartData>('/charts/sankey', analysisData, { signal, timeout: 30000 })
  return data
}

export const downloadPdfReport = async (analysisData: AnalysisData): Promise<void> => {
  const response = await api.post('/reports/pdf', analysisData, {
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  const name = analysisData.project_info?.name || 'report'
  link.setAttribute('download', `LCA_${name}.pdf`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export const sendChatMessage = async (question: string): Promise<string> => {
  const { data } = await api.post<{ answer: string }>('/chat', { question })
  return data.answer
}

export const findSimilarAudits = async (materials: string[]): Promise<AuditResult[]> => {
  const { data } = await api.get<AuditResult[]>('/audits/similar', {
    params: { materials: materials.join(',') },
  })
  return data
}
