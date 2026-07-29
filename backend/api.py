import base64
import json
import logging
import os
import re
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eagerly initialize the transcription model on application startup."""
    logger.info("Starting AgentX API — initializing transcription engine …")
    try:
        from backend.live_transcript import get_engine

        engine = get_engine()
        success = engine.ensure_initialized()
        if success:
            logger.info(
                "Transcription engine ready (backend: %s)", engine.backend
            )
        else:
            logger.error(
                "Transcription engine failed to initialize: %s",
                engine._init_error or "unknown error",
            )
    except Exception as exc:
        logger.error("Transcription engine init raised: %s", exc)
    yield
    logger.info("Shutting down AgentX API.")


app = FastAPI(title="AgentX API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Organization Knowledge Module routes
from modules.organization_knowledge.routes import router as org_knowledge_router
app.include_router(org_knowledge_router)


class TranscriptRequest(BaseModel):
    transcript: str


class TopicRequest(BaseModel):
    topic: str


class JournalRequest(BaseModel):
    entry: str


class TaskCreateRequest(BaseModel):
    title: str


class TaskUpdateRequest(BaseModel):
    title: str | None = None
    done: bool | None = None


class EmailRequest(BaseModel):
    action: str | None = None
    email: dict | None = None


class KnowledgeRequest(BaseModel):
    query: str = ""


class PipelineRequest(BaseModel):
    transcript: str = ""
    use_sample: bool = True


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


# ------------------------------------------------------------------
# Task Management (Journal AI → Todo List)
# ------------------------------------------------------------------

@app.get("/tasks")
def get_all_tasks():
    """Return all tasks + aggregate stats."""
    from backend.journal_ai import get_task_stats, get_tasks

    return {
        "tasks": get_tasks(),
        "stats": get_task_stats(),
    }


@app.post("/tasks")
def add_task(payload: TaskCreateRequest):
    """Create a new task."""
    from backend.journal_ai import create_task

    return create_task(payload.title)


@app.put("/tasks/{task_id}")
def edit_task(task_id: str, payload: TaskUpdateRequest):
    """Update a task (title and/or done status)."""
    from backend.journal_ai import update_task

    update_data = {}
    if payload.title is not None:
        update_data["title"] = payload.title
    if payload.done is not None:
        update_data["done"] = payload.done

    result = update_task(task_id, update_data)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@app.delete("/tasks/{task_id}")
def remove_task(task_id: str):
    """Delete a task."""
    from backend.journal_ai import delete_task

    if not delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted", "id": task_id}


@app.get("/tasks/stats")
def task_stats():
    """Return only the aggregate statistics."""
    from backend.journal_ai import get_task_stats

    return get_task_stats()


# ------------------------------------------------------------------
# Action Agent — unites pending tasks + unread emails
# ------------------------------------------------------------------

@app.get("/action-agent")
def action_agent():
    """Return pending tasks + unread email count + stats for the Action Agent dashboard."""
    from backend.journal_ai import get_task_stats, get_tasks

    tasks = get_tasks()
    stats = get_task_stats()

    # Try to scan unread emails (gracefully handle missing config)
    unread_count = 0
    unread_emails = []
    email_error = None

    try:
        from backend import main as backend_main

        if os.path.exists("credentials.json"):
            creds = backend_main.get_credentials()
            gmail = backend_main.build("gmail", "v1", credentials=creds)
            results = gmail.users().messages().list(
                userId="me", labelIds=["UNREAD"], maxResults=10
            ).execute()
            messages = results.get("messages", [])
            unread_count = len(messages)
            for msg in messages:
                msg_data = gmail.users().messages().get(
                    userId="me", id=msg["id"], format="full"
                ).execute()
                payload_data = msg_data.get("payload", {})
                headers = payload_data.get("headers", [])
                text = _decode_email_body(payload_data) or msg_data.get("snippet", "")
                unread_emails.append({
                    "id": msg["id"],
                    "subject": _email_header(headers, "Subject") or "No subject",
                    "sender": _email_header(headers, "From") or "Unknown",
                    "preview": text[:300],
                })
    except Exception as e:
        email_error = str(e)

    return {
        "tasks": [t for t in tasks if not t["done"]],
        "task_stats": stats,
        "unread_count": unread_count,
        "unread_emails": unread_emails,
        "email_error": email_error,
    }


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """Receive browser-recorded audio and return transcribed text."""
    from backend.live_transcript import transcribe_audio_file

    audio_bytes = await file.read()
    print(f"[transcribe] Received {len(audio_bytes)} bytes, filename={file.filename}, content_type={file.content_type}")
    result = transcribe_audio_file(audio_bytes)
    if result.get("error"):
        print(f"[transcribe] Error: {result['error']}")
    else:
        print(f"[transcribe] Transcript ({len(result.get('segments', []))} segments): {result.get('transcript', '')[:100]}")
    return result


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
    # Handle actions (calendar / notion) first
    if payload.action and payload.email:
        try:
            from backend import main as backend_main
        except ModuleNotFoundError:
            import sys
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import main as backend_main

        email = payload.email
        start = email.get("start")
        if not start:
            raise HTTPException(status_code=400, detail="Selected email has no detected date/time.")
        start_time = datetime.fromisoformat(start)
        title = email.get("title") or email.get("subject") or "AgentX Event"
        intent_type = email.get("detected_type") or email.get("type") or "task"
        duration_minutes = int(email.get("duration_minutes") or 60)
        try:
            if payload.action == "calendar":
                backend_main.create_calendar_event(title, start_time, intent_type, duration_minutes)
            elif payload.action == "notion":
                backend_main.add_to_notion(title, start_time)
            else:
                raise HTTPException(status_code=400, detail="Unsupported action requested.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to execute {payload.action} action: {e}")
        return {"status": "ok", "message": f"{payload.action} action completed."}

    # Scan emails — gracefully handle missing credentials / config
    try:
        from backend import main as backend_main
    except ModuleNotFoundError:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import main as backend_main

    # Check if credentials exist
    if not os.path.exists("credentials.json"):
        return {
            "scanned_count": 0,
            "detected_emails": [],
            "upcoming_events": _load_json_list("events.json"),
            "error": "Gmail API not configured. Place a 'credentials.json' file from Google Cloud Console in the project root.",
        }

    try:
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
    except Exception as e:
        return {
            "scanned_count": 0,
            "detected_emails": [],
            "upcoming_events": _load_json_list("events.json"),
            "error": f"Gmail scan failed: {e}",
        }


@app.post("/pipeline/run")
def pipeline_run(payload: PipelineRequest):
    from backend.knowledge_hub import store_meeting
    from backend.meeting_summarizer import summarize_meeting

    sample_transcript = (
        "Alice: We need to finish the AgentX meeting summarizer.\n"
        "Bob: I'll integrate the Notion API.\n"
        "Charlie: I'll test the system tomorrow.\n"
        "Alice: Let's present it Friday.\n"
    )

    transcript = payload.transcript if payload.transcript.strip() else sample_transcript

    summary = summarize_meeting(transcript)
    store_meeting(summary)

    notion_status = "Notion token not configured"
    try:
        from backend.notion_writer import write_summary
        write_summary(summary)
        notion_status = "Summary saved to Notion"
    except Exception as e:
        notion_status = f"Notion write skipped: {e}"

    return {
        "summary_data": summary,
        "notion": {"message": notion_status},
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

