"""Journal AI — Persistent Todo List with Statistics & Streak Tracking."""

import json
from datetime import date, datetime
from pathlib import Path

TASKS_FILE = Path(__file__).resolve().parent.parent / "tasks.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_tasks():
    """Load all tasks from the JSON file."""
    if not TASKS_FILE.exists():
        return []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_tasks(tasks):
    """Persist the task list to the JSON file."""
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)


# ---------------------------------------------------------------------------
# Public CRUD
# ---------------------------------------------------------------------------

def create_task(title: str) -> dict:
    """Create a new task and persist it."""
    tasks = _load_tasks()
    task = {
        "id": _next_id(tasks),
        "title": title.strip(),
        "done": False,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    tasks.append(task)
    _save_tasks(tasks)
    return task


def get_tasks() -> list[dict]:
    """Return the full task list."""
    return _load_tasks()


def update_task(task_id: str, data: dict) -> dict | None:
    """Update a task's title and/or done status. Returns updated task or None."""
    tasks = _load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            if "title" in data:
                task["title"] = data["title"].strip()
            if "done" in data:
                task["done"] = bool(data["done"])
                task["completed_at"] = (
                    datetime.now().isoformat() if task["done"] else None
                )
            _save_tasks(tasks)
            return task
    return None


def delete_task(task_id: str) -> bool:
    """Remove a task by id. Returns True if deleted, False if not found."""
    tasks = _load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        return False
    _save_tasks(new_tasks)
    return True


# ---------------------------------------------------------------------------
# Statistics & streak
# ---------------------------------------------------------------------------

def get_task_stats() -> dict:
    """Compute aggregate statistics and current streak."""
    tasks = _load_tasks()
    total = len(tasks)
    completed = sum(1 for t in tasks if t["done"])
    pending = total - completed
    progress = round((completed / total) * 100, 1) if total > 0 else 0.0

    # Build set of dates on which at least one task was completed
    completed_dates: set[date] = set()
    for t in tasks:
        if t["done"] and t.get("completed_at"):
            try:
                completed_dates.add(datetime.fromisoformat(t["completed_at"]).date())
            except (ValueError, TypeError):
                pass

    # Walk backwards from today counting consecutive days
    streak = 0
    today = date.today()
    check = today
    while check in completed_dates:
        streak += 1
        check = date.fromordinal(check.toordinal() - 1)

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "progress": progress,
        "streak": streak,
    }


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _next_id(tasks: list) -> str:
    """Generate a simple unique id string."""
    if not tasks:
        return "1"
    existing = set()
    for t in tasks:
        try:
            existing.add(int(t["id"]))
        except (ValueError, KeyError):
            pass
    candidate = 1
    while candidate in existing:
        candidate += 1
    return str(candidate)

