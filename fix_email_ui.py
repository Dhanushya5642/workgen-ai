"""Fix EmailIntelligence.jsx - proper JSX structure"""
content = r"""import { useMemo, useState } from "react";
import ApiResponsePanel from "../components/ApiResponsePanel";
import ResultCard from "../components/ResultCard";
import { scanEmails } from "../services/api";

function normalizeEmailScan(data) {
  return {
    emails: data?.detected_emails || data?.emails || [],
    events: data?.upcoming_events || data?.events || data?.calendar || [],
    scannedCount: data?.scanned_count || data?.count || 0,
  };
}

function typeTone(type) {
  const value = String(type || "Unknown").toLowerCase();
  if (value.includes("meeting"))
    return "bg-sky-500/15 text-sky-300 border-sky-400/30";
  if (value.includes("task"))
    return "bg-amber-500/15 text-amber-300 border-amber-400/30";
  if (value.includes("exam"))
    return "bg-rose-500/15 text-rose-300 border-rose-400/30";
  return "bg-emerald-500/15 text-emerald-300 border-emerald-400/30";
}

export default function EmailIntelligence({ theme }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [rawResponse, setRawResponse] = useState(null);
  const [payload, setPayload] = useState({
    emails: [],
    events: [],
    scannedCount: 0,
  });

  const summary = useMemo(
    () => ({
      meetings: payload.emails.filter((item) =>
        String(item.detected_type || item.type)
          .toLowerCase()
          .includes("meeting"),
      ).length,
      tasks: payload.emails.filter((item) =>
        String(item.detected_type || item.type)
          .toLowerCase()
          .includes("task"),
      ).length,
    }),
    [payload.emails],
  );

  const scan = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await scanEmails();
      setRawResponse(response);
      if (response?.error) {
        setError(response.error);
      }
      setPayload(normalizeEmailScan(response));
    } catch (err) {
      setError(err.message || "Unable to scan emails.");
    } finally {
      setLoading(false);
    }
  };

  const cardClass =
    theme === "dark"
      ? "border-white/10 bg-white/5"
      : "border-slate-200 bg-white/85";

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        {[
          { label: "Scanned Emails", value: payload.scannedCount || payload.emails.length },
          { label: "Meeting Signals", value: summary.meetings },
          { label: "Task Signals", value: summary.tasks },
        ].map((stat) => (
          <div key={stat.label} className={`rounded-[28px] border p-5 shadow-xl ${cardClass}`}>
            <p className="text-sm text-slate-400">{stat.label}</p>
            <p className="mt-3 text-3xl font-semibold">{stat.value}</p>
          </div>
        ))}
      </section>

      <ResultCard
        title="Email Intelligence"
        subtitle="Scan Gmail, classify intent, and automatically add to Calendar + Notion."
        theme={theme}
        actions={
          <button type="button" onClick={scan} disabled={loading}
            className="rounded-2xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60">
            {loading ? "Scanning..." : "Scan Emails"}
          </button>
        }>
        <div className="space-y-4">
          {error ? (
            <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
              {error}
            </div>
          ) : null}
          {!error && payload.emails.length > 0 ? (
            <div className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
              ✓ Emails auto-processed - Calendar and Notion created automatically.
            </div>
          ) : null}
        </div>
      </ResultCard>

      <div className="grid gap-6 xl:grid-cols-[1.35fr_0.85fr]">
        <ResultCard title="Detected Emails" subtitle="AI classified and auto-processed emails." theme={theme}>
          <div className="space-y-4">
            {payload.emails.length === 0 ? (
              <div className={`rounded-3xl border border-dashed p-8 text-center text-sm text-slate-400 ${cardClass}`}>
                Click <span className="font-semibold text-slate-200">Scan Emails</span> to load classified inbox results.
              </div>
            ) : (
              payload.emails.map((email, index) => {
                const type = email.detected_type || email.type || "Unknown";
                const actions = email.auto_actions || [];
                return (
                  <div key={`email-${index}`} className={`rounded-3xl border p-5 ${cardClass}`}>
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div className="space-y-2">
                        <div className="text-lg font-semibold">{email.subject || "Untitled Email"}</div>
                        <div className="text-sm text-slate-400">{email.sender || email.from || "Unknown sender"}</div>
                      <div className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${typeTone(type)}`}>
                        {type}
                      </div>
                    <p className="mt-4 text-sm leading-7 text-slate-400">
                      {email.preview || email.snippet || email.body || "No email preview returned by the backend."}
                    </p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {actions.length > 0 ? actions.map((action, ai) => (
                        <span key={`action-${ai}`}
                          className={`rounded-lg px-3 py-1 text-xs font-medium ${
                            action.includes("calendar_added") ? "bg-emerald-500/15 text-emerald-300" :
                            action.includes("notion_added") ? "bg-violet-500/15 text-violet-300" :
                            action.includes("skipped") ? "bg-amber-500/10 text-amber-300" :
                            "bg-slate-500/10 text-slate-400"
                          }`}>
                          {action.includes("calendar_added") ? "✓ Calendar" : null}
                          {action.includes("notion_added") ? "✓ Notion" : null}
                          {action.includes("skipped") ? "⚠ Skipped" : null}
                        </span>
                      )) : email.start ? (
                        <span className="text-xs text-cyan-400">Auto-processing on scan...</span>
                      ) : (
                        <span className="text-xs text-amber-400">No date found - skipped auto-processing</span>
                      )}
                    </div>
                );
              })
            )}
          </div>
        </ResultCard>

        <ResultCard title="Upcoming Events" theme={theme}>
          <div className="space-y-3">
            {payload.events.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/10 px-4 py-5 text-sm text-slate-400">
                Upcoming events will appear here after the scan returns calendar data.
              </div>
            ) : (
              payload.events.map((event, index) => (
                <div key={`event-${index}`} className={`rounded-2xl border p-4 ${cardClass}`}>
                  <div className="font-semibold">{event.title || event.summary || "Untitled event"}</div>
                  <div className="mt-1 text-sm text-slate-400">{event.datetime || event.start_time || event.start || "Time not provided"}</div>
                  <div className="mt-3 text-xs uppercase tracking-[0.2em] text-cyan-400">{event.source || "calendar sync"}</div>
              ))
            )}
          </div>
        </ResultCard>
      </div>
  );
}
"""

with open('agentx-frontend/src/pages/EmailIntelligence.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Written successfully")

# Verify basic JSX structure
opens = content.count("<div")
closes = content.count("</div")
print(f"div opens: {opens}, closes: {closes}, diff: {opens - closes}")

opens_rc = content.count("<ResultCard")
closes_rc = content.count("</ResultCard")
print(f"ResultCard opens: {opens_rc}, closes: {closes_rc}, diff: {opens_rc - closes_rc}")
