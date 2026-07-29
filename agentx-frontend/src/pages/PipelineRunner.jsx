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
            className={`w-full rounded-3xl border px-4 py-4 text-sm outline-none transition ${
              theme === 'dark'
                ? 'border-white/10 bg-slate-950/60 text-slate-100 placeholder:text-slate-500'
                : 'border-[#D3CBB8] bg-[#FAF8F5] text-stone-800 placeholder:text-stone-400 focus:border-clay'
            }`}
          />

          {error ? (
            <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{error}</div>
          ) : null}

          <button
            type="submit"
            disabled={loading}
            className={`rounded-2xl px-5 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
              theme === 'dark' ? 'bg-cyan-400 text-slate-950 hover:bg-cyan-300' : 'bg-clay text-white hover:bg-clay/90'
            }`}
          >
            {loading ? 'Running pipeline…' : 'Run Pipeline'}
          </button>
        </form>
      </ResultCard>

      {result?.summary_data ? (
        <ResultCard title="Pipeline Summary" subtitle="Returned by /pipeline/run" theme={theme}>
          <div className="space-y-4 text-sm text-slate-300">
            <div>
              <div className={`text-xs uppercase tracking-[0.2em] ${theme === 'dark' ? 'text-cyan-400' : 'text-forest font-semibold'}`}>Summary</div>
              <p className={`mt-2 leading-7 ${theme === 'dark' ? 'text-slate-300' : 'text-stone-700'}`}>{result.summary_data.summary || 'No summary returned.'}</p>
            </div>
            <div>
              <div className={`text-xs uppercase tracking-[0.2em] ${theme === 'dark' ? 'text-cyan-400' : 'text-forest font-semibold'}`}>Notion</div>
              <p className={`mt-2 leading-7 ${theme === 'dark' ? 'text-slate-300' : 'text-stone-700'}`}>{result.notion?.message || 'No Notion status returned.'}</p>
            </div>
          </div>
        </ResultCard>
      ) : null}

      {/* <ApiResponsePanel data={result} theme={theme} /> */}
    </div>
  )
}