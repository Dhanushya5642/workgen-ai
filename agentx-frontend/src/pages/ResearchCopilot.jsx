import { useState } from "react";
import ApiResponsePanel from "../components/ApiResponsePanel";
import ResultCard from "../components/ResultCard";
import { generateResearch } from "../services/api";

function renderList(items) {
  if (!items?.length)
    return <p className="text-sm text-slate-400">No data yet.</p>;

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

export default function ResearchCopilot({ theme }) {
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const submit = async () => {
    if (!topic.trim()) {
      setError("Please enter a research topic.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await generateResearch(topic);
      setResult(response);
    } catch (err) {
      setError(err.message || "Unable to generate research package.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <ResultCard
        title="Research Copilot"
        subtitle="Generate structured academic or market research frameworks from a single prompt."
        theme={theme}
        actions={
          <button
            type="button"
            onClick={submit}
            disabled={loading}
            className="rounded-2xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Generating…" : "Generate Research"}
          </button>
        }
      >
        <div className="space-y-4">
          <input
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Enter a research topic..."
            className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none transition ${
              theme === "dark"
                ? "border-white/10 bg-slate-950/70 text-slate-50 placeholder:text-slate-500 focus:border-cyan-400/40"
                : "border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:border-cyan-400"
            }`}
          />
          {error ? (
            <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
              {error}
            </div>
          ) : null}
        </div>
      </ResultCard>

      <div className="grid gap-6 xl:grid-cols-2">
        <ResultCard
          title="Overview"
          subtitle="High-level framing"
          theme={theme}
        >
          <p className="text-sm leading-7 text-slate-300">
            {result?.overview || "No overview generated yet."}
          </p>
        </ResultCard>
        <ResultCard
          title="Outline"
          subtitle="Suggested research structure"
          theme={theme}
        >
          {renderList(result?.outline)}
        </ResultCard>
        <ResultCard
          title="Key Concepts"
          subtitle="Important ideas to explore"
          theme={theme}
        >
          {renderList(result?.key_concepts)}
        </ResultCard>
        <ResultCard
          title="Research Questions"
          subtitle="What to investigate"
          theme={theme}
        >
          {renderList(result?.research_questions)}
        </ResultCard>
      </div>

      <ResultCard
        title="Citations"
        
        theme={theme}
      >
        {renderList(result?.citations)}
      </ResultCard>

      {/* <ApiResponsePanel data={result} theme={theme} /> */}
    </div>
  );
}
