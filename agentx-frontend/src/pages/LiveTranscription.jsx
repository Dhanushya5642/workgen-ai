import { useEffect, useMemo, useState } from 'react'
import ApiResponsePanel from '../components/ApiResponsePanel'
import ResultCard from '../components/ResultCard'
import { startTranscription } from '../services/api'

function normalizeSegments(data) {
  if (Array.isArray(data?.segments)) return data.segments.map((item) => item.text || item)
  if (Array.isArray(data?.chunks)) return data.chunks.map((item) => item.text || item)
  if (Array.isArray(data?.lines)) return data.lines
  if (typeof data?.transcript === 'string') return data.transcript.split(/\n+/).filter(Boolean)
  return []
}

export default function LiveTranscription({ theme }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [segments, setSegments] = useState([])
  const [visibleSegments, setVisibleSegments] = useState([])
  const [meta, setMeta] = useState(null)

  useEffect(() => {
    if (!segments.length) return undefined

    setVisibleSegments([])
    let index = 0

    const timer = setInterval(() => {
      setVisibleSegments((current) => [...current, segments[index]])
      index += 1
      if (index >= segments.length) clearInterval(timer)
    }, 350)

    return () => clearInterval(timer)
  }, [segments])

  const transcript = useMemo(() => visibleSegments.join(' '), [visibleSegments])

  const submit = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await startTranscription()
      setMeta(response)
      setSegments(normalizeSegments(response))
    } catch (err) {
      setError(err.message || 'Unable to start live transcription.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <ResultCard
        title="Live Transcription"
        subtitle="Trigger the backend listener and stream transcript output into a live panel."
        theme={theme}
        actions={
          <button
            type="button"
            onClick={submit}
            disabled={loading}
            className="rounded-2xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? 'Listening…' : 'Start Listening'}
          </button>
        }
      >
        <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400">
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-emerald-300">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-300" />
            {loading ? 'Microphone active' : 'Ready to listen'}
          </span>
          <span>Panel supports transcript strings, chunks, or segment arrays</span>
        </div>
        {error ? <div className="mt-4 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{error}</div> : null}
      </ResultCard>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <ResultCard title="Real-time Transcript" subtitle="Streaming display" theme={theme}>
          <div
            className={`min-h-[320px] rounded-[28px] border p-5 text-sm leading-8 ${
              theme === 'dark' ? 'border-white/10 bg-slate-950/70 text-slate-200' : 'border-slate-200 bg-slate-50 text-slate-700'
            }`}
          >
            {transcript || 'The live transcript will appear here once the backend returns speech-to-text output.'}
          </div>
        </ResultCard>

        <ResultCard title="Session Metadata" theme={theme}>
          <div className="space-y-3 text-sm text-slate-300">
            {meta ? (
              Object.entries(meta)
                .filter(([key]) => !['segments', 'chunks', 'lines', 'transcript'].includes(key))
                .map(([key, value]) => (
                  <div
                    key={key}
                    className={`rounded-2xl border px-4 py-3 ${
                      theme === 'dark' ? 'border-white/10 bg-white/5' : 'border-slate-200 bg-slate-50 text-slate-700'
                    }`}
                  >
                    <span className="font-semibold capitalize">{key.replace(/_/g, ' ')}:</span>{' '}
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </div>
                ))
            ) : (
              <div className="rounded-2xl border border-dashed border-white/10 px-4 py-5 text-sm text-slate-400">
                No session metadata yet.
              </div>
            )}
          </div>
        </ResultCard>
      </div>

      {/* <ApiResponsePanel data={meta} theme={theme} /> */}
    </div>
  )
}