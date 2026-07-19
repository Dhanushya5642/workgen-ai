import ast
import json
import re
from datetime import date

try:
    import ollama
except ImportError:
    ollama = None


# ---------------- EMOTION ANALYZER ---------------- #

def _normalize_emotion_data(data):

    if not isinstance(data, dict):
        return None

    def _to_int(value, default):
        try:
            return int(value)
        except Exception:
            return default

    return {
        "emotion": str(data.get("emotion", "unknown")),
        "stress_level": _to_int(data.get("stress_level", 5), 5),
        "focus_level": _to_int(data.get("focus_level", 5), 5),
        "suggestion": str(data.get("suggestion", "Unable to analyze emotion")),
    }

def analyze_emotion(text):

    prompt = f"""
You are an emotional intelligence AI.

Analyze the journal entry and return JSON only.

Format:

{{
"emotion":"",
"stress_level":1,
"focus_level":1,
"suggestion":""
}}

Journal Entry:
{text}
"""

    response = ollama.chat(
        model="phi3",
        messages=[{"role":"user","content":prompt}]
    )

    raw = response["message"]["content"]

    candidates = [raw]

    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        candidates.append(match.group())

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            normalized = _normalize_emotion_data(parsed)
            if normalized:
                return normalized
        except Exception:
            pass

        try:
            parsed = ast.literal_eval(candidate)
            normalized = _normalize_emotion_data(parsed)
            if normalized:
                return normalized
        except Exception:
            pass

    return {
        "emotion":"unknown",
        "stress_level":5,
        "focus_level":5,
        "suggestion":"Unable to analyze emotion"
    }


# ---------------- MOOD LOGGER ---------------- #

def log_mood(data):

    try:
        with open("mood_log.json","r") as f:
            history = json.load(f)

    except:
        history = []

    entry = {
        "date": str(date.today()),
        "emotion": data["emotion"],
        "stress": data["stress_level"],
        "focus": data["focus_level"]
    }

    history.append(entry)

    with open("mood_log.json","w") as f:
        json.dump(history,f,indent=2)

    print("Mood logged successfully.")


# ---------------- TASK PRIORITIZER ---------------- #

def adjust_tasks(tasks, stress_level):

    if stress_level >= 7:

        print("\nHigh stress detected → prioritizing easier tasks\n")

        tasks_sorted = sorted(tasks, key=lambda x: x["difficulty"])

    else:

        print("\nNormal mode → prioritizing important tasks\n")

        tasks_sorted = sorted(tasks, key=lambda x: x["priority"])

    return tasks_sorted


# ---------------- REMINDER STRATEGY ---------------- #

def reminder_strategy(stress):

    if stress >= 8:
        return "Minimal reminders to reduce stress"

    elif stress >= 5:
        return "Normal reminder schedule"

    else:
        return "Motivational reminders enabled"


# ---------------- RUN FUNCTION (IMPORTANT) ---------------- #

def run_journal_ai():

    print("==== AgentX Private AI Journal ====\n")

    entry = input("Write your journal entry:\n\n")

    emotion_data = analyze_emotion(entry)

    print("\nEmotion Analysis")
    print("-------------------")

    print("Emotion:", emotion_data["emotion"])
    print("Stress Level:", emotion_data["stress_level"])
    print("Focus Level:", emotion_data["focus_level"])
    print("Suggestion:", emotion_data["suggestion"])


    log_mood(emotion_data)


    tasks = [
        {"task":"Finish research paper","priority":1,"difficulty":9},
        {"task":"Reply to emails","priority":3,"difficulty":2},
        {"task":"Prepare presentation slides","priority":2,"difficulty":6},
        {"task":"Read research articles","priority":4,"difficulty":3}
    ]


    print("\nOriginal Task List")
    print("-------------------")

    for t in tasks:
        print("-", t["task"])


    optimized = adjust_tasks(tasks, emotion_data["stress_level"])


    print("\nOptimized Task Order")
    print("-------------------")

    for t in optimized:
        print("-", t["task"])


    print("\nReminder Strategy")
    print("-------------------")

    print(reminder_strategy(emotion_data["stress_level"]))
    