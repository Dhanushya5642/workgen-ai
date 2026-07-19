import { useState } from "react";
import ApiResponsePanel from "../components/ApiResponsePanel";
import ResultCard from "../components/ResultCard";
import { summarizeMeeting } from "../services/api";

function renderItems(items) {
  if (!items?.length)
    return <p className="text-sm text-slate-400">No items returned.</p>;

  return (
    <ul className="space-y-2 text-sm leading-7 text-slate-300">
      {items.map((item, index) => (
        <li
          key={`${String(item)}-${index}`}
          className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3"
        >
          {typeof item === "object" ? JSON.stringify(item) : item}
        </li>
      ))}
    </ul>
  );
}

export default function MeetingIntelligence({ theme }) {
  const [transcript, setTranscript] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const submit = async () => {
    if (!transcript.trim()) {
      setError("Please paste a meeting transcript first.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await summarizeMeeting(transcript);
      setResult(response);
    } catch (err) {
      setError(err.message || "Unable to generate meeting summary.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <ResultCard
        title="Meeting Intelligence"
        subtitle="Summarize transcripts and surface decisions, action items, and next steps."
        theme={theme}
        actions={
          <button
            type="button"
            onClick={submit}
            disabled={loading}
            className="rounded-2xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Generating…" : "Generate Summary"}
          </button>
        }
      >
        <textarea
          value={transcript}
          onChange={(event) => setTranscript(event.target.value)}
          placeholder="Paste your meeting transcript here..."
          className={`min-h-[240px] w-full rounded-[28px] border px-5 py-4 text-sm outline-none transition ${
            theme === "dark"
              ? "border-white/10 bg-slate-950/70 text-slate-50 placeholder:text-slate-500 focus:border-cyan-400/40"
              : "border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:border-cyan-400"
          }`}
        />
        {error ? (
          <div className="mt-4 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
            {error}
          </div>
        ) : null}
      </ResultCard>

      <div className="grid gap-6 xl:grid-cols-2">
        <ResultCard title="Summary" subtitle="Executive recap" theme={theme}>
          <p className="text-sm leading-7 text-slate-300">
            {result?.summary || "No summary generated yet."}
          </p>
        </ResultCard>
        <ResultCard
          title="Decisions"
          subtitle="Committed choices"
          theme={theme}
        >
          {renderItems(result?.decisions)}
        </ResultCard>
        <ResultCard
          title="Action Items"
          subtitle="Assigned or implied work"
          theme={theme}
        >
          {renderItems(result?.actions || result?.action_items)}
        </ResultCard>
        <ResultCard
          title="Next Steps"
          subtitle="Follow-up momentum"
          theme={theme}
        >
          {renderItems(result?.next_steps)}
        </ResultCard>
      </div>

      {/* <ApiResponsePanel data={result} theme={theme} /> */}
    </div>
  );
}
