import { useState } from 'react'
import ApiResponsePanel from '../components/ApiResponsePanel'
import ResultCard from '../components/ResultCard'
import { runMeetingPipeline } from '../services/api'

export default function PipelineRunner({ theme }) {
  const [transcript, setTranscript] = useState('')
  const [useSample, setUseSample] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const submit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await runMeetingPipeline(transcript, useSample)
      setResult(response)
    } catch (err) {
      setError(err.message || 'Unable to run the meeting pipeline.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <ResultCard
        title="Meeting Pipeline"
        subtitle="Run transcript summarization and Notion sync through the backend pipeline endpoint."
        theme={theme}
      >
        <form className="space-y-4" onSubmit={submit}>
          <label className="flex items-center gap-3 text-sm text-slate-400">
            <input
              type="checkbox"
              checked={useSample}
              onChange={(event) => setUseSample(event.target.checked)}
            />
            Use bundled sample transcript when no custom transcript is provided
          </label>

          <textarea
            value={transcript}
            onChange={(event) => setTranscript(event.target.value)}
            rows={10}
            placeholder="Paste a meeting transcript here to run the full pipeline..."
            className="w-full rounded-3xl border border-white/10 bg-slate-950/60 px-4 py-4 text-sm text-slate-100 outline-none ring-0 placeholder:text-slate-500"
          />

          {error ? (
            <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{error}</div>
          ) : null}

          <button
            type="submit"
            disabled={loading}
            className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? 'Running pipeline…' : 'Run Pipeline'}
          </button>
        </form>
      </ResultCard>

      {result?.summary_data ? (
        <ResultCard title="Pipeline Summary" subtitle="Returned by /pipeline/run" theme={theme}>
          <div className="space-y-4 text-sm text-slate-300">
            <div>
              <div className="text-xs uppercase tracking-[0.2em] text-cyan-400">Summary</div>
              <p className="mt-2 leading-7">{result.summary_data.summary || 'No summary returned.'}</p>
            </div>
            <div>
              <div className="text-xs uppercase tracking-[0.2em] text-cyan-400">Notion</div>
              <p className="mt-2 leading-7">{result.notion?.message || 'No Notion status returned.'}</p>
            </div>
          </div>
        </ResultCard>
      ) : null}

      {/* <ApiResponsePanel data={result} theme={theme} /> */}
    </div>
  )
}