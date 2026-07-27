import base64
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(title="AgentX API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranscriptRequest(BaseModel):
    transcript: str


class TopicRequest(BaseModel):
    topic: str


class JournalRequest(BaseModel):
    entry: str


class EmailRequest(BaseModel):
    action: str | None = None
    email: dict | None = None


class KnowledgeRequest(BaseModel):
    query: str = ""


def _decode_email_body(payload):
    body = payload.get("body", {}).get("data")
    if body:
        return base64.urlsafe_b64decode(body).decode(errors="ignore")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                return base64.urlsafe_b64decode(data).decode(errors="ignore")
    return ""


def _email_header(headers, name):
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _parse_email_details(text, backend_main):
    lowered = text.lower()
    detected_type = backend_main.classify_email_type(text)
    if "exam" in lowered:
        detected_type = "exam"
    elif "meeting" in lowered:
        detected_type = "meeting"
    if detected_type == "none":
        return None
    date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text)
    if not date_match:
        return None
    date_obj = datetime.strptime(date_match.group(1), "%d/%m/%Y")
    time_match = re.search(r"(\d{1,2}:\d{2}\s*(am|pm))", lowered)
    time_obj = datetime.strptime(time_match.group(1), "%I:%M %p").time() if time_match else datetime.strptime("09:00", "%H:%M").time()
    duration_match = re.search(r"(\d+(\.\d+)?)\s*hour", lowered)
    duration_minutes = int(float(duration_match.group(1)) * 60) if duration_match else 60
    start = datetime.combine(date_obj.date(), time_obj).replace(tzinfo=backend_main.IST)
    return {
        "detected_type": detected_type,
        "title": detected_type.capitalize(),
        "start": start.isoformat(),
        "duration_minutes": duration_minutes,
    }


def _load_json_list(path):
    file_path = Path(path)
    if not file_path.exists():
        return []
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return []


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/summarize")
def summarize(payload: TranscriptRequest):
    from backend.knowledge_hub import store_meeting
    from backend.meeting_summarizer import summarize_meeting

    result = summarize_meeting(payload.transcript)
    store_meeting(result)
    return result


@app.post("/research")
def research(payload: TopicRequest):
    from backend.research_engine import generate_research_package

    return generate_research_package(payload.topic)


@app.post("/journal")
def journal(payload: JournalRequest):
    from backend.journal_ai import adjust_tasks, analyze_emotion, log_mood, reminder_strategy

    emotion_data = analyze_emotion(payload.entry)
    log_mood(emotion_data)
    tasks = [
        {"task": "Finish research paper", "priority": 1, "difficulty": 9},
        {"task": "Reply to emails", "priority": 3, "difficulty": 2},
        {"task": "Prepare presentation slides", "priority": 2, "difficulty": 6},
        {"task": "Read research articles", "priority": 4, "difficulty": 3},
    ]
    return {
        **emotion_data,
        "optimized_tasks": adjust_tasks(tasks, emotion_data["stress_level"]),
        "reminder_strategy": reminder_strategy(emotion_data["stress_level"]),
    }


@app.post("/transcribe")
def transcribe():
    from backend.live_transcript import duration, model, record_audio, samplerate

    audio_data = record_audio()
    segments, _ = model.transcribe(audio_data, language="en")
    lines = [segment.text.strip() for segment in segments if getattr(segment, "text", "").strip()]
    return {
        "transcript": " ".join(lines),
        "segments": [{"text": line} for line in lines],
        "duration": duration,
        "sample_rate": samplerate,
    }


@app.post("/knowledge-hub")
def knowledge_hub(payload: KnowledgeRequest):
    query = payload.query.strip().lower()
    entries = _load_json_list("knowledge_base.json")
    if query:
        entries = [entry for entry in entries if query in json.dumps(entry).lower()]
    normalized = []
    for entry in reversed(entries[-10:]):
        data = entry.get("data", {}) if isinstance(entry, dict) else {}
        normalized.append({
            "type": entry.get("type", "entry"),
            "title": data.get("title") or entry.get("type", "Knowledge item").title(),
            "summary": data.get("summary") or json.dumps(data or entry, ensure_ascii=False),
        })
    return {"entries": normalized}


@app.post("/scan-emails")
def scan_emails(payload: EmailRequest):
    try:
        from backend import main as backend_main
    except ModuleNotFoundError:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import main as backend_main

    if payload.action and payload.email:
        email = payload.email
        start = email.get("start")
        if not start:
            raise HTTPException(status_code=400, detail="Selected email has no detected date/time.")
        start_time = datetime.fromisoformat(start)
        title = email.get("title") or email.get("subject") or "AgentX Event"
        intent_type = email.get("detected_type") or email.get("type") or "task"
        duration_minutes = int(email.get("duration_minutes") or 60)
        if payload.action == "calendar":
            backend_main.create_calendar_event(title, start_time, intent_type, duration_minutes)
        elif payload.action == "notion":
            backend_main.add_to_notion(title, start_time)
        else:
            raise HTTPException(status_code=400, detail="Unsupported action requested.")
        return {"status": "ok", "message": f"{payload.action} action completed."}

    creds = backend_main.get_credentials()
    gmail = backend_main.build("gmail", "v1", credentials=creds)
    results = gmail.users().messages().list(userId="me", labelIds=["UNREAD"], maxResults=5).execute()
    messages = results.get("messages", [])
    detected_emails = []
    for message in messages:
        message_data = gmail.users().messages().get(userId="me", id=message["id"], format="full").execute()
        payload_data = message_data.get("payload", {})
        headers = payload_data.get("headers", [])
        text = _decode_email_body(payload_data) or message_data.get("snippet", "")
        parsed = _parse_email_details(text, backend_main)
        if not parsed:
            continue
        detected_emails.append({
            "id": message["id"],
            "subject": _email_header(headers, "Subject") or parsed["title"],
            "sender": _email_header(headers, "From"),
            "preview": text[:500],
            **parsed,
        })

    return {
        "scanned_count": len(messages),
        "detected_emails": detected_emails,
        "upcoming_events": _load_json_list("events.json"),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
