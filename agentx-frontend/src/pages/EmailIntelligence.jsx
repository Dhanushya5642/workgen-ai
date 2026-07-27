import { useMemo, useState } from 'react'
import ApiResponsePanel from '../components/ApiResponsePanel'
import ResultCard from '../components/ResultCard'
import { runEmailAction, scanEmails } from '../services/api'

function normalizeEmailScan(data) {
  return {
    emails: data?.detected_emails || data?.emails || [],
    events: data?.upcoming_events || data?.events || data?.calendar || [],
    scannedCount: data?.scanned_count || data?.count || 0,
  }
}

function typeTone(type) {
  const value = String(type || 'Unknown').toLowerCase()
  if (value.includes('meeting')) return 'bg-sky-500/15 text-sky-300 border-sky-400/30'
  if (value.includes('task')) return 'bg-amber-500/15 text-amber-300 border-amber-400/30'
  if (value.includes('exam')) return 'bg-rose-500/15 text-rose-300 border-rose-400/30'
  return 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30'
}

export default function EmailIntelligence({ theme }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [actionMessage, setActionMessage] = useState('')
  const [busyAction, setBusyAction] = useState('')
  const [rawResponse, setRawResponse] = useState(null)
  const [payload, setPayload] = useState({ emails: [], events: [], scannedCount: 0 })

  const summary = useMemo(() => ({
    meetings: payload.emails.filter((item) => String(item.detected_type || item.type).toLowerCase().includes('meeting')).length,
    tasks: payload.emails.filter((item) => String(item.detected_type || item.type).toLowerCase().includes('task')).length,
  }), [payload.emails])

  const scan = async () => {
    setLoading(true)
    setError('')
    setActionMessage('')

    try {
      const response = await scanEmails()
      setRawResponse(response)
      setPayload(normalizeEmailScan(response))
    } catch (err) {
      setError(err.message || 'Unable to scan emails.')
    } finally {
      setLoading(false)
    }
  }

  const handleAction = async (action, email, index) => {
    const key = `${action}-${index}`
    setBusyAction(key)
    setActionMessage('')
    setError('')

    try {
      const response = await runEmailAction(action, email)
      setRawResponse(response)
      setActionMessage(`${action === 'calendar' ? 'Calendar' : 'Notion'} action submitted for “${email.subject || 'Untitled'}”.`)
    } catch (err) {
      setError(err.message || `Unable to complete ${action} action.`)
    } finally {
      setBusyAction('')
    }
  }

  const cardClass = theme === 'dark' ? 'border-white/10 bg-white/5' : 'border-slate-200 bg-white/85'

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        {[
          { label: 'Scanned Emails', value: payload.scannedCount || payload.emails.length },
          { label: 'Meeting Signals', value: summary.meetings },
          { label: 'Task Signals', value: summary.tasks },
        ].map((stat) => (
          <div key={stat.label} className={`rounded-[28px] border p-5 shadow-xl ${cardClass}`}>
            <p className="text-sm text-slate-400">{stat.label}</p>
            <p className="mt-3 text-3xl font-semibold">{stat.value}</p>
          </div>
        ))}
      </section>

      <ResultCard
        title="Email Intelligence"
        subtitle="Scan Gmail, classify intent, and surface calendar-ready opportunities."
        theme={theme}
        actions={
          <button
            type="button"
            onClick={scan}
            disabled={loading}
            className="rounded-2xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? 'Scanning…' : 'Scan Emails'}
          </button>
        }
      >
        <div className="space-y-4">
          {/* <p className="max-w-3xl text-sm leading-7 text-slate-400">
            The frontend calls <code className="rounded bg-black/10 px-1.5 py-0.5">POST /scan-emails</code> and renders email classifications, downstream actions, and upcoming event context.
          </p> */}
          {error ? <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{error}</div> : null}
          {actionMessage ? <div className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">{actionMessage}</div> : null}
        </div>
      </ResultCard>

      <div className="grid gap-6 xl:grid-cols-[1.35fr_0.85fr]">
        <ResultCard title="Detected Emails" subtitle="AI classified emails ready for action." theme={theme}>
          <div className="space-y-4">
            {payload.emails.length === 0 ? (
              <div className={`rounded-3xl border border-dashed p-8 text-center text-sm text-slate-400 ${cardClass}`}>
                Click <span className="font-semibold text-slate-200">Scan Emails</span> to load classified inbox results.
              </div>
            ) : (
              payload.emails.map((email, index) => {
                const type = email.detected_type || email.type || 'Unknown'
                return (
                  <div key={`${email.subject || 'email'}-${index}`} className={`rounded-3xl border p-5 ${cardClass}`}>
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div className="space-y-2">
                        <div className="text-lg font-semibold">{email.subject || 'Untitled Email'}</div>
                        <div className="text-sm text-slate-400">{email.sender || email.from || 'Unknown sender'}</div>
                      </div>
                      <div className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${typeTone(type)}`}>
                        {type}
                      </div>
                    </div>

                    <p className="mt-4 text-sm leading-7 text-slate-400">
                      {email.preview || email.snippet || email.body || 'No email preview returned by the backend.'}
                    </p>

                    <div className="mt-5 flex flex-wrap gap-3">
                      {email.auto_added && email.auto_added.length > 0 ? (
                        email.auto_added.map((action) => (
                          <span
                            key={action}
                            className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300"
                          >
                            ✓ {action === 'calendar' ? 'Added to Calendar' : 'Saved to Notion'}
                          </span>
                        ))
                      ) : (
                        <p className="text-xs text-slate-500 italic">No auto-actions performed</p>
                      )}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </ResultCard>

        <ResultCard title="Upcoming Events"  theme={theme}>
          <div className="space-y-3">
            {payload.events.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/10 px-4 py-5 text-sm text-slate-400">
                Upcoming events will appear here after the scan returns calendar data.
              </div>
            ) : (
              payload.events.map((event, index) => (
                <div key={`${event.title || event.summary || 'event'}-${index}`} className={`rounded-2xl border p-4 ${cardClass}`}>
                  <div className="font-semibold">{event.title || event.summary || 'Untitled event'}</div>
                  <div className="mt-1 text-sm text-slate-400">{event.datetime || event.start_time || event.start || 'Time not provided'}</div>
                  <div className="mt-3 text-xs uppercase tracking-[0.2em] text-cyan-400">{event.source || 'calendar sync'}</div>
                </div>
              ))
            )}
          </div>
        </ResultCard>
      </div>

      {/* <ApiResponsePanel data={rawResponse} theme={theme} /> */}
    </div>
  )
}