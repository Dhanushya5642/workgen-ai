import { useState } from "react";
import ResultCard from "../components/ResultCard";
import { searchKnowledgeHub } from "../services/api";

export default function KnowledgeHub({ theme }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [entries, setEntries] = useState([]);

  const dark = theme === "dark";

  const handleSearch = async () => {
    const trimmed = query.trim();

    if (!trimmed) {
      setError("Please enter a search term.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await searchKnowledgeHub(trimmed);
      setEntries(response?.entries || []);
    } catch (err) {
      setError(err.message || "Unable to search the knowledge hub.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <ResultCard
        title="Knowledge Hub"
        subtitle="Search saved insights, meeting notes, and stored knowledge snippets."
        theme={theme}
        actions={
          <button
            type="button"
            onClick={handleSearch}
            disabled={loading}
            className={`rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
              dark
                ? "bg-cyan-400 text-slate-950 hover:bg-cyan-300"
                : "bg-clay text-white hover:bg-clay/90"
            }`}
          >
            {loading ? "Searching…" : "Search Hub"}
          </button>
        }
      >
        <div className="space-y-4">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search the knowledge hub..."
            className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none transition ${
              dark
                ? "border-white/10 bg-slate-950/70 text-slate-50 placeholder:text-slate-500 focus:border-cyan-400/40"
                : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-800 placeholder:text-stone-400 focus:border-clay"
            }`}
          />
          {error ? (
            <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
              {error}
            </div>
          ) : null}
        </div>
      </ResultCard>

      <div className="grid gap-4">
        {entries.length === 0 ? (
          <ResultCard title="Results" subtitle="No results yet" theme={theme}>
            <p
              className={`text-sm ${dark ? "text-slate-300" : "text-stone-700"}`}
            >
              Search for a topic to surface recent entries from the shared
              knowledge base.
            </p>
          </ResultCard>
        ) : (
          entries.map((entry, index) => (
            <ResultCard
              key={`${entry.title || entry.type || "entry"}-${index}`}
              title={entry.title || entry.type || "Knowledge Entry"}
              subtitle={entry.type || "entry"}
              theme={theme}
            >
              <p
                className={`text-sm leading-7 ${dark ? "text-slate-300" : "text-stone-700"}`}
              >
                {entry.summary || "No summary available."}
              </p>
            </ResultCard>
          ))
        )}
      </div>
    </div>
  );
}
