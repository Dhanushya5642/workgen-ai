import { useEffect, useState } from "react";
import ResultCard from "../components/ResultCard";
import {
  createTask,
  deleteTask,
  getActionAgentDashboard,
  updateTask,
} from "../services/api";

export default function JournalAI({ theme }) {
  const [taskInput, setTaskInput] = useState("");
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    pending: 0,
    progress: 0,
    streak: 0,
  });
  const [unreadEmails, setUnreadEmails] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [emailError, setEmailError] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const dark = theme === "dark";

  // ---------- Load everything from backend ----------
  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await getActionAgentDashboard();
      setTasks(data.tasks || []);
      setStats(data.task_stats || stats);
      setUnreadEmails(data.unread_emails || []);
      setUnreadCount(data.unread_count ?? 0);
      if (data.email_error) {
        setEmailError(data.email_error);
      } else {
        setEmailError(null);
      }
    } catch {
      setError("Failed to load dashboard. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  // ---------- Add task ----------
  const addTask = async () => {
    const value = taskInput.trim();
    if (!value) {
      setError("Please enter a task first.");
      return;
    }
    setError("");
    setTaskInput("");
    try {
      await createTask(value);
      await loadDashboard();
    } catch {
      setError("Failed to add task.");
    }
  };

  // ---------- Toggle done ----------
  const markDone = async (id) => {
    try {
      await updateTask(id, { done: true });
      await loadDashboard();
    } catch {
      setError("Failed to update task.");
    }
  };

  // ---------- Remove task ----------
  const removeTask = async (id) => {
    try {
      await deleteTask(id);
      await loadDashboard();
    } catch {
      setError("Failed to delete task.");
    }
  };

  // ---------- Progress bar color ----------
  const progressColor =
    stats.progress >= 80
      ? "bg-emerald-500"
      : stats.progress >= 50
        ? "bg-amber-500"
        : "bg-rose-500";

  return (
    <div className="space-y-6">
      {/* ---- Stats Bar ---- */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="⏳ Pending Tasks"
          value={stats.pending}
          theme={theme}
          dark={dark}
        />
        <StatCard
          label="📧 Unread Emails"
          value={unreadCount}
          theme={theme}
          dark={dark}
        />
        <StatCard
          label="✅ Completed"
          value={stats.completed}
          theme={theme}
          dark={dark}
        />
        <StatCard
          label="🔥 Streak"
          value={`${stats.streak} day${stats.streak !== 1 ? "s" : ""}`}
          theme={theme}
          dark={dark}
        />
      </div>

      {/* ---- Progress Bar ---- */}
      <div
        className={`rounded-[28px] border p-5 shadow-xl ${
          dark ? "border-white/10 bg-white/5" : "border-[#D3CBB8] bg-[#FAF8F5]"
        }`}
      >
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className={dark ? "text-slate-400" : "text-stone-500"}>
            Overall Progress
          </span>
          <span className="font-semibold">{stats.progress}%</span>
        </div>
        <div
          className={`h-3 w-full overflow-hidden rounded-full ${
            dark ? "bg-slate-800" : "bg-stone-200"
          }`}
        >
          <div
            className={`h-full rounded-full transition-all duration-500 ${progressColor}`}
            style={{ width: `${Math.min(stats.progress, 100)}%` }}
          />
        </div>
      </div>

      {/* ---- Error banner ---- */}
      {error ? (
        <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
          {error}
        </div>
      ) : null}

      {/* ---- Task Input Row ---- */}
      <ResultCard
        title="Action Agent"
        subtitle="Add tasks, track pending items, and monitor unread emails — all in one place."
        theme={theme}
        actions={
          <button
            type="button"
            onClick={addTask}
            disabled={loading}
            className={`rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
              dark
                ? "bg-cyan-400 text-slate-950 hover:bg-cyan-300"
                : "bg-clay text-white hover:bg-clay/90"
            }`}
          >
            Add Task
          </button>
        }
      >
        <input
          value={taskInput}
          onChange={(event) => setTaskInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              addTask();
            }
          }}
          placeholder="Add a task, e.g. Prepare standup notes"
          className={`w-full rounded-[28px] border px-5 py-4 text-sm outline-none transition ${
            dark
              ? "border-white/10 bg-slate-950/70 text-slate-50 placeholder:text-slate-500 focus:border-cyan-400/40"
              : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-800 placeholder:text-stone-400 focus:border-clay"
          }`}
        />
      </ResultCard>

      {/* ---- Two-column layout: Tasks | Emails ---- */}
      <div className="grid gap-6 xl:grid-cols-2">
        {/* ---- PENDING TASKS COLUMN ---- */}
        <ResultCard
          title="⏳ Pending Tasks"
          subtitle={`${tasks.length} item${tasks.length !== 1 ? "s" : ""} waiting`}
          theme={theme}
        >
          {loading ? (
            <div className="rounded-2xl border border-dashed px-4 py-6 text-sm text-slate-400">
              Loading…
            </div>
          ) : tasks.length === 0 ? (
            <div className="rounded-2xl border border-dashed px-4 py-6 text-sm text-slate-400">
              No pending tasks. Add one above!
            </div>
          ) : (
            <div className="space-y-3">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className={`flex items-center justify-between gap-3 rounded-2xl border px-4 py-3 ${
                    dark
                      ? "border-white/10 bg-white/5"
                      : "border-[#D3CBB8] bg-[#FAF8F5]"
                  }`}
                >
                  <span
                    className={`text-left text-sm ${
                      dark ? "text-slate-100" : "text-stone-800"
                    }`}
                  >
                    {task.title}
                  </span>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => markDone(task.id)}
                      className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${
                        dark
                          ? "bg-emerald-500/20 text-emerald-300"
                          : "bg-emerald-100 text-emerald-700"
                      }`}
                    >
                      Done
                    </button>
                    <button
                      type="button"
                      onClick={() => removeTask(task.id)}
                      className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${
                        dark
                          ? "bg-rose-500/15 text-rose-300"
                          : "bg-rose-100 text-rose-700"
                      }`}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ResultCard>

        {/* ---- UNREAD EMAILS COLUMN ---- */}
        <ResultCard
          title="📧 Unread Emails"
          subtitle={
            emailError
              ? "Gmail sync unavailable"
              : `${unreadCount} unread message${unreadCount !== 1 ? "s" : ""}`
          }
          theme={theme}
        >
          {loading ? (
            <div className="rounded-2xl border border-dashed px-4 py-6 text-sm text-slate-400">
              Loading…
            </div>
          ) : emailError ? (
            <div className="rounded-2xl border border-amber-400/30 bg-amber-500/10 px-4 py-6 text-sm text-amber-300">
              <p className="font-semibold">Gmail API not available</p>
              <p className="mt-1 text-xs opacity-80">
                {emailError.includes("credentials.json")
                  ? "Place a credentials.json file in the project root to enable email scanning."
                  : emailError}
              </p>
            </div>
          ) : unreadEmails.length === 0 ? (
            <div className="rounded-2xl border border-dashed px-4 py-6 text-sm text-slate-400">
              No unread emails. All caught up!
            </div>
          ) : (
            <div className="space-y-3">
              {unreadEmails.map((email) => (
                <div
                  key={email.id}
                  className={`rounded-2xl border px-4 py-3 ${
                    dark
                      ? "border-white/10 bg-white/5"
                      : "border-[#D3CBB8] bg-[#FAF8F5]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p
                        className={`truncate text-sm font-semibold ${
                          dark ? "text-slate-100" : "text-stone-800"
                        }`}
                      >
                        {email.subject}
                      </p>
                      <p
                        className={`mt-0.5 truncate text-xs ${
                          dark ? "text-slate-400" : "text-stone-500"
                        }`}
                      >
                        {email.sender}
                      </p>
                    </div>
                    <span
                      className={`inline-flex h-2 w-2 shrink-0 rounded-full ${
                        dark ? "bg-cyan-400" : "bg-clay"
                      }`}
                    />
                  </div>
                  <p
                    className={`mt-2 line-clamp-2 text-xs leading-5 ${
                      dark ? "text-slate-500" : "text-stone-500"
                    }`}
                  >
                    {email.preview || "No preview available."}
                  </p>
                </div>
              ))}
            </div>
          )}
        </ResultCard>
      </div>
    </div>
  );
}

// ---- Small reusable stat card ----
function StatCard({ label, value, theme, dark }) {
  return (
    <div
      className={`rounded-[28px] border p-5 shadow-xl transition ${
        dark
          ? "border-white/10 bg-white/5"
          : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-850"
      }`}
    >
      <p className={`text-sm ${dark ? "text-slate-400" : "text-stone-500"}`}>
        {label}
      </p>
      <p className="mt-3 text-lg font-semibold leading-7">{value}</p>
    </div>
  );
}
