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
            className={`rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
              theme === 'dark' ? 'bg-cyan-400 text-slate-950 hover:bg-cyan-300' : 'bg-clay text-white hover:bg-clay/90'
            }`}
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
              : 'border-[#D3CBB8] bg-[#FAF8F5] text-stone-850 placeholder:text-stone-400 focus:border-clay'
          }`}
        />
        {error ? <div className="mt-4 rounded-2xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">{error}</div> : null}
      </ResultCard>

      <ResultCard title="Results" subtitle="Backend-driven knowledge retrieval" theme={theme}>
        <div className="space-y-3">
          {entries.length === 0 ? (
            <div className={`rounded-2xl border border-dashed px-4 py-6 text-sm ${
              theme === 'dark' ? 'border-white/10 text-slate-400' : 'border-[#D3CBB8] text-stone-500'
            }`}>
              Search results will appear here when the optional Knowledge Hub endpoint is available.
            </div>
          ) : (
            entries.map((entry, index) => (
              <div
                key={`${entry.title || entry.type || 'entry'}-${index}`}
                className={`rounded-2xl border p-4 transition ${
                  theme === 'dark' ? 'border-white/10 bg-white/5' : 'border-[#D3CBB8] bg-[#FAF8F5]'
                }`}
              >
                <div className="font-semibold">{entry.title || entry.type || 'Knowledge item'}</div>
                <div className={`mt-2 text-sm leading-7 ${theme === 'dark' ? 'text-slate-400' : 'text-stone-600'}`}>{entry.summary || entry.content || JSON.stringify(entry)}</div>
              </div>
            ))
          )}
        </div>
      </ResultCard>

      {/* <ApiResponsePanel data={result} theme={theme} /> */}
    </div>
  )
}