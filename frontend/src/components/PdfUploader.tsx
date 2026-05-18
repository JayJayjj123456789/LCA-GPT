import { useState, useRef, type FormEvent, type DragEvent } from 'react'
import { analyzePdf } from '../api'
import type { AnalysisData } from '../api'

interface Props {
  onAnalyzed: (data: AnalysisData) => void
}

export default function PdfUploader({ onAnalyzed }: Props) {
  const [files, setFiles]       = useState<File[]>([])
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentFile, setCurrentFile] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const addFiles = (newFiles: FileList | null) => {
    if (!newFiles) return
    const pdfs = Array.from(newFiles).filter(f => f.type === 'application/pdf')
    if (pdfs.length === 0) {
      setError('Only PDF files are accepted')
      return
    }
    setFiles(prev => [...prev, ...pdfs])
    setError(null)
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleDrop = (e: DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    addFiles(e.dataTransfer.files)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (files.length === 0) return
    setLoading(true)
    setError(null)
    setProgress(0)

    const interval = setInterval(() => {
      setProgress(p => (p < 85 ? p + Math.random() * 8 : p))
    }, 600)

    try {
      // Analyze each file and merge results
      const results: AnalysisData[] = []
      for (let i = 0; i < files.length; i++) {
        setCurrentFile(files[i].name)
        const data = await analyzePdf(files[i])
        results.push(data)
        setProgress(Math.round(((i + 1) / files.length) * 90))
      }

      // Merge all results into one
      const merged = mergeResults(results)
      setProgress(100)
      onAnalyzed(merged)
      setFiles([])
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed. Check backend connection.')
    } finally {
      clearInterval(interval)
      setLoading(false)
      setCurrentFile('')
    }
  }

  const totalSize = files.reduce((sum, f) => sum + f.size, 0)

  return (
    <div className="card p-5 space-y-4">
      <div className="noise-bg" />
      <div className="relative z-10 space-y-4">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary" style={{ fontSize: 18, fontVariationSettings: "'FILL' 1" }}>
              description
            </span>
            <h3 className="text-section-label">Data Ingestion</h3>
          </div>
          {files.length > 0 && (
            <span className="text-xs text-on-surface-variant bg-surface-container-highest px-2 py-1 rounded-full">
              {files.length} file{files.length > 1 ? 's' : ''} · {(totalSize / 1024).toFixed(0)} KB
            </span>
          )}
        </div>

        {/* Drop Zone */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`rounded-xl p-6 text-center cursor-pointer transition-all duration-200 border-2 border-dashed select-none ${
              dragOver
                ? 'border-primary bg-primary/8 scale-[1.01]'
                : files.length > 0
                  ? 'border-primary-container bg-primary-container/10'
                  : 'border-surface-container-highest hover:border-outline hover:bg-surface-container/60'
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf"
              multiple
              onChange={(e) => addFiles(e.target.files)}
              className="hidden"
            />

            {files.length > 0 ? (
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-primary-container/20 flex items-center justify-center mx-auto">
                  <span className="material-symbols-outlined text-primary" style={{ fontSize: 20, fontVariationSettings: "'FILL' 1" }}>
                    picture_as_pdf
                  </span>
                </div>
                <div className="space-y-1.5 max-h-[120px] overflow-y-auto">
                  {files.map((f, i) => (
                    <div key={i} className="flex items-center justify-between gap-2 bg-surface-container/50 rounded-lg px-3 py-1.5">
                      <span className="text-xs text-on-surface truncate max-w-[180px]">{f.name}</span>
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); removeFile(i) }}
                        className="text-on-surface-variant/50 hover:text-error transition-colors cursor-pointer shrink-0"
                      >
                        <span className="material-symbols-outlined" style={{ fontSize: 14 }}>close</span>
                      </button>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-on-surface-variant">
                  Drop more files or <span className="text-primary font-semibold">browse</span> to add
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-surface-container-highest flex items-center justify-center mx-auto">
                  <span className="material-symbols-outlined text-on-surface-variant" style={{ fontSize: 20 }}>
                    upload_file
                  </span>
                </div>
                <div>
                  <p className="text-sm text-on-surface-variant">
                    Drop your PDFs here or{' '}
                    <span className="text-primary font-semibold">browse</span>
                  </p>
                  <p className="text-xs text-on-surface-variant/50 mt-1">
                    Upload multiple files — PO · Spec Sheet · Sustainability Report · BOM
                  </p>
                </div>
                <div className="flex justify-center gap-2">
                  {(['Scope 1', 'Scope 2', 'Scope 3'] as const).map((s, idx) => (
                    <span key={s} className={`chip chip-scope${idx + 1}`}>{s}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Progress Bar */}
          {loading && (
            <div className="space-y-1.5 animate-fade-in">
              <div className="flex justify-between text-xs text-on-surface-variant">
                <span className="truncate max-w-[200px]">{currentFile || 'Analyzing…'}</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{ width: `${progress}%`, transition: 'width 0.6s cubic-bezier(0.23,1,0.32,1)' }}
                />
              </div>
              <p className="text-xs text-on-surface-variant/50 text-center">
                Analyzing {files.length} file{files.length > 1 ? 's' : ''} via AI…
              </p>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={files.length === 0 || loading}
            className={`w-full py-3 rounded-xl text-xs font-semibold uppercase tracking-widest transition-all duration-200 cursor-pointer flex items-center justify-center gap-2 ${
              files.length === 0 || loading
                ? 'bg-surface-container text-on-surface-variant/30 cursor-not-allowed'
                : 'bg-primary-container text-on-primary-container hover:bg-primary hover:text-on-primary active:scale-[0.98]'
            }`}
          >
            {loading ? (
              <>
                <svg className="animate-spin w-3.5 h-3.5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Running Audit…
              </>
            ) : (
              <>
                <span className="material-symbols-outlined" style={{ fontSize: 16, fontVariationSettings: "'FILL' 1" }}>
                  play_circle
                </span>
                Run AI Carbon Audit {files.length > 1 ? `(${files.length} files)` : ''}
              </>
            )}
          </button>

          {/* Error */}
          {error && (
            <div className="animate-fade-in flex items-start gap-2.5 border border-error/25 bg-error-container/15 text-error p-3 rounded-xl text-xs leading-relaxed">
              <span className="material-symbols-outlined shrink-0" style={{ fontSize: 16 }}>warning</span>
              {error}
            </div>
          )}
        </form>
      </div>
    </div>
  )
}

/** Merge multiple AnalysisData results into one */
function mergeResults(results: AnalysisData[]): AnalysisData {
  if (results.length === 1) return results[0]

  const merged: AnalysisData = {
    project_info: results[0].project_info,
    materials: [],
    energy: [],
    transport: [],
    total_estimated_co2: 0,
    optimization_score: 0,
    recommendations: [],
    summary: '',
  }

  // Deduplicate materials by name — sum amounts
  const matMap = new Map<string, { amount: number; ef: number; unit: string; note: string }>()
  for (const r of results) {
    for (const m of r.materials || []) {
      const existing = matMap.get(m.name)
      if (existing) {
        existing.amount += m.amount
      } else {
        matMap.set(m.name, { amount: m.amount, ef: m.emission_factor, unit: m.unit, note: m.note })
      }
    }
  }
  merged.materials = Array.from(matMap.entries()).map(([name, v]) => ({
    name,
    amount: v.amount,
    unit: v.unit,
    emission_factor: v.ef,
    note: v.note,
  }))

  // Deduplicate energy by type
  const enMap = new Map<string, { usage: number; ef: number; unit: string; note: string }>()
  for (const r of results) {
    for (const e of r.energy || []) {
      const existing = enMap.get(e.type)
      if (existing) {
        existing.usage += e.usage
      } else {
        enMap.set(e.type, { usage: e.usage, ef: e.emission_factor, unit: e.unit, note: e.note })
      }
    }
  }
  merged.energy = Array.from(enMap.entries()).map(([type, v]) => ({
    type,
    usage: v.usage,
    unit: v.unit,
    emission_factor: v.ef,
    note: v.note,
  }))

  // Deduplicate transport by method
  const trMap = new Map<string, { distance: number; ef: number; unit: string; note: string }>()
  for (const r of results) {
    for (const t of r.transport || []) {
      const existing = trMap.get(t.method)
      if (existing) {
        existing.distance += t.distance
      } else {
        trMap.set(t.method, { distance: t.distance, ef: t.emission_factor, unit: t.unit, note: t.note })
      }
    }
  }
  merged.transport = Array.from(trMap.entries()).map(([method, v]) => ({
    method,
    distance: v.distance,
    unit: v.unit,
    emission_factor: v.ef,
    note: v.note,
  }))

  // Sum totals
  merged.total_estimated_co2 = results.reduce((sum, r) => sum + (r.total_estimated_co2 || 0), 0)
  merged.optimization_score = Math.round(results.reduce((sum, r) => sum + (r.optimization_score || 0), 0) / results.length)

  // Merge unique recommendations
  const recSet = new Set<string>()
  for (const r of results) {
    for (const rec of r.recommendations || []) {
      recSet.add(rec)
    }
  }
  merged.recommendations = Array.from(recSet)

  merged.summary = `Merged analysis from ${results.length} documents. Total CO₂e: ${merged.total_estimated_co2.toFixed(2)} kgCO₂e`

  return merged
}
