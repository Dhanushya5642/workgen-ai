import { useMemo, useState } from "react";
import ResultCard from "../components/ResultCard";

export default function JournalAI({ theme }) {
  const [taskInput, setTaskInput] = useState("");
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");

  const addTask = () => {
    const value = taskInput.trim();

    if (!value) {
      setError("Please enter a task first.");
      return;
    }

    setError("");
    setTasks((prev) => [
      {
        id: crypto.randomUUID(),
        title: value,
        done: false,
        createdAt: Date.now(),
      },
      ...prev,
    ]);
    setTaskInput("");
  };

  const toggleTask = (id) => {
    setTasks((prev) =>
      prev.map((task) =>
        task.id === id ? { ...task, done: !task.done } : task,
      ),
    );
  };

  const removeTask = (id) => {
    setTasks((prev) => prev.filter((task) => task.id !== id));
  };

  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((task) => task.done).length;
  const pendingTasks = totalTasks - completedTasks;
  const progress =
    totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  const filteredTasks = useMemo(() => {
    if (filter === "done") return tasks.filter((task) => task.done);
    if (filter === "active") return tasks.filter((task) => !task.done);
    return tasks;
  }, [tasks, filter]);

  const stats = [
    { label: "Total Tasks", value: totalTasks },
    { label: "Completed", value: completedTasks },
    { label: "Pending", value: pendingTasks },
    { label: "Progress", value: `${progress}%` },
  ];

  return (
    <div className="space-y-6">
      <ResultCard
        title="Journal AI"
        subtitle="Plan your day with a smart to-do list and track progress live."
        theme={theme}
        actions={
          <button
            type="button"
            onClick={addTask}
            className={`rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
              theme === "dark"
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
            theme === "dark"
              ? "border-white/10 bg-slate-950/70 text-slate-50 placeholder:text-slate-500 focus:border-cyan-400/40"
              : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-800 placeholder:text-stone-400 focus:border-clay"
          }`}
        />
        {error ? (
          <div className="mt-4 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
            {error}
          </div>
        ) : null}
      </ResultCard>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((metric) => (
          <div
            key={metric.label}
            className={`rounded-[28px] border p-5 shadow-xl transition ${
              theme === "dark"
                ? "border-white/10 bg-white/5"
                : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-850"
            }`}
          >
            <p
              className={`text-sm ${theme === "dark" ? "text-slate-400" : "text-stone-500"}`}
            >
              {metric.label}
            </p>
            <p className="mt-3 text-lg font-semibold leading-7">
              {metric.value}
            </p>
          </div>
        ))}
      </div>

      <ResultCard
        title="Task Board"
        subtitle="Track, complete, and clean up your tasks."
        theme={theme}
      >
        <div className="mb-4 flex flex-wrap gap-2">
          {[
            { id: "all", label: "All" },
            { id: "active", label: "Active" },
            { id: "done", label: "Completed" },
          ].map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setFilter(item.id)}
              className={`rounded-xl border px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.15em] transition ${
                filter === item.id
                  ? theme === "dark"
                    ? "border-cyan-400/40 bg-cyan-400/15 text-cyan-300"
                    : "border-clay/40 bg-clay/10 text-clay"
                  : theme === "dark"
                    ? "border-white/10 bg-white/5 text-slate-300 hover:bg-white/10"
                    : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-600 hover:bg-[#F3EFE4]"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {filteredTasks.length === 0 ? (
          <div
            className={`rounded-2xl border border-dashed px-4 py-6 text-sm ${theme === "dark" ? "border-white/10 text-slate-400" : "border-[#D3CBB8] text-stone-500"}`}
          >
            No tasks in this view yet.
          </div>
        ) : (
          <div className="space-y-3">
            {filteredTasks.map((task) => (
              <div
                key={task.id}
                className={`flex items-center justify-between gap-3 rounded-2xl border px-4 py-3 ${
                  theme === "dark"
                    ? "border-white/10 bg-white/5"
                    : "border-[#D3CBB8] bg-[#FAF8F5]"
                }`}
              >
                <button
                  type="button"
                  onClick={() => toggleTask(task.id)}
                  className={`text-left text-sm transition ${
                    task.done
                      ? theme === "dark"
                        ? "text-slate-400 line-through"
                        : "text-stone-500 line-through"
                      : theme === "dark"
                        ? "text-slate-100"
                        : "text-stone-800"
                  }`}
                >
                  {task.title}
                </button>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => toggleTask(task.id)}
                    className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${
                      task.done
                        ? theme === "dark"
                          ? "bg-slate-700 text-slate-100"
                          : "bg-stone-200 text-stone-700"
                        : theme === "dark"
                          ? "bg-emerald-500/20 text-emerald-300"
                          : "bg-emerald-100 text-emerald-700"
                    }`}
                  >
                    {task.done ? "Undo" : "Done"}
                  </button>
                  <button
                    type="button"
                    onClick={() => removeTask(task.id)}
                    className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${theme === "dark" ? "bg-rose-500/15 text-rose-300" : "bg-rose-100 text-rose-700"}`}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </ResultCard>
    </div>
  );
}
