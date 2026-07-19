import { useState } from 'react'
import ApiResponsePanel from '../components/ApiResponsePanel'
import ResultCard from '../components/ResultCard'
import { searchKnowledgeHub } from '../services/api'

export default function KnowledgeHub({ theme }) {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const search = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await searchKnowledgeHub(query)
      setResult(response)
    } catch (err) {
      setError(err.message || 'Knowledge Hub endpoint is not available yet.')
    } finally {
      setLoading(false)
    }
  }

  const entries = result?.entries || result?.results || result?.items || []

  return (
    <div className="space-y-6">
      <ResultCard
        title="Knowledge Hub"
        subtitle="Optional module for searching saved knowledge artifacts across AgentX workflows."
        theme={theme}
        actions={
          <button
            type="button"
            onClick={search}
            disabled={loading}
            className="rounded-2xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? 'Searching…' : 'Search Hub'}
          </button>
        }
      >
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search meetings, research, or saved notes..."
          className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none transition ${
            theme === 'dark'
              ? 'border-white/10 bg-slate-950/70 text-slate-50 placeholder:text-slate-500 focus:border-cyan-400/40'
              : 'border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:border-cyan-400'
          }`}
        />
        {error ? <div className="mt-4 rounded-2xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">{error}</div> : null}
      </ResultCard>

      <ResultCard title="Results" subtitle="Backend-driven knowledge retrieval" theme={theme}>
        <div className="space-y-3">
          {entries.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-white/10 px-4 py-6 text-sm text-slate-400">
              Search results will appear here when the optional Knowledge Hub endpoint is available.
            </div>
          ) : (
            entries.map((entry, index) => (
              <div
                key={`${entry.title || entry.type || 'entry'}-${index}`}
                className={`rounded-2xl border p-4 ${
                  theme === 'dark' ? 'border-white/10 bg-white/5' : 'border-slate-200 bg-white/85'
                }`}
              >
                <div className="font-semibold">{entry.title || entry.type || 'Knowledge item'}</div>
                <div className="mt-2 text-sm leading-7 text-slate-400">{entry.summary || entry.content || JSON.stringify(entry)}</div>
              </div>
            ))
          )}
        </div>
      </ResultCard>

      {/* <ApiResponsePanel data={result} theme={theme} /> */}
    </div>
  )
}