import { useState } from 'react'
import ApiResponsePanel from '../components/ApiResponsePanel'
import ResultCard from '../components/ResultCard'
import { analyzeJournal } from '../services/api'

export default function JournalAI({ theme }) {
  const [entry, setEntry] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const submit = async () => {
    if (!entry.trim()) {
      setError('Please enter a journal note to analyze.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await analyzeJournal(entry)
      setResult(response)
    } catch (err) {
      setError(err.message || 'Unable to analyze journal entry.')
    } finally {
      setLoading(false)
    }
  }

  const metrics = [
    { label: 'Emotion', value: result?.emotion || result?.mood || '—' },
    { label: 'Stress Level', value: result?.stress_level || result?.stress || '—' },
    { label: 'Focus Level', value: result?.focus_level || result?.focus || '—' },
    { label: 'Suggestion', value: result?.suggestion || '—' },
  ]

  return (
    <div className="space-y-6">
      <ResultCard
        title="Journal AI"
        subtitle="Analyze mood, stress, and focus from reflective writing."
        theme={theme}
        actions={
          <button
            type="button"
            onClick={submit}
            disabled={loading}
            className={`rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
              theme === 'dark' ? 'bg-cyan-400 text-slate-950 hover:bg-cyan-300' : 'bg-clay text-white hover:bg-clay/90'
            }`}
          >
            {loading ? 'Analyzing…' : 'Analyze Emotion'}
          </button>
        }
      >
        <textarea
          value={entry}
          onChange={(event) => setEntry(event.target.value)}
          placeholder="Write your journal entry here..."
          className={`min-h-[220px] w-full rounded-[28px] border px-5 py-4 text-sm outline-none transition ${
            theme === 'dark'
              ? 'border-white/10 bg-slate-950/70 text-slate-50 placeholder:text-slate-500 focus:border-cyan-400/40'
              : 'border-[#D3CBB8] bg-[#FAF8F5] text-stone-800 placeholder:text-stone-400 focus:border-clay'
          }`}
        />
        {error ? <div className="mt-4 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{error}</div> : null}
      </ResultCard>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className={`rounded-[28px] border p-5 shadow-xl transition ${
              theme === 'dark' ? 'border-white/10 bg-white/5' : 'border-[#D3CBB8] bg-[#FAF8F5] text-stone-850'
            }`}
          >
            <p className={`text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-stone-500'}`}>{metric.label}</p>
            <p className="mt-3 text-lg font-semibold leading-7">{metric.value}</p>
          </div>
        ))}
      </div>

      {/* <ApiResponsePanel data={result} theme={theme} /> */}
    </div>
  )
}