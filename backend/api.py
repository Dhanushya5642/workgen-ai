import base64
import json
import os
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
    """
    Parse an email to extract type, date, time and duration.
    Supports dd/mm/yyyy, mm-dd-yyyy, yyyy-mm-dd date formats,
    hh:mm am/pm and 24h time formats, and X hour/min duration formats.
    Falls back to a keyword-based classifier if the AI classifier returns 'none'.
    """
    lowered = text.lower()
    detected_type = backend_main.classify_email_type(text)
    if detected_type == "none":
        keyword_map = {
            "meeting": [r"\bmeeting\b", r"\bmeet\b", r"\bagenda\b", r"\bconference\b",
                        r"\bstandup\b", r"\bworkshop\b", r"\bsync\b", r"\bgather\b",
                        r"\bschedule\b", r"\bappointment\b", r"\breminder\b",
                        r"\bzoom\b", r"\bteams\b", r"\bvideo call\b", r"\bcall\b"],
            "exam": [r"\bexam\b", r"\btest\b", r"\bquiz\b", r"\bassessment\b",
                     r"\bfinal\b", r"\bpractical\b", r"\bgrade\b", r"\bscore\b",
                     r"\bresult\b", r"\bmark\b", r"\bpaper\b", r"\bevaluation\b"],
            "interview": [r"\binterview\b", r"\brecruiter\b", r"\bhiring\b",
                          r"\bplacement\b", r"\bhr\b", r"\bpanel\b", r"\boffer\b"],
            "payment": [r"\bpayment\b", r"\bbill\b", r"\binvoice\b", r"\breceipt\b",
                        r"\bdue\b", r"\btransaction\b", r"\bpay\b", r"\bamount\b",
                        r"\bpaid\b", r"\brefund\b", r"\bsubscription\b"],
            "task": [r"\btask\b", r"\bdeadline\b", r"\bassignment\b",
                     r"\bsubmission\b", r"\bproject\b", r"\bdeliverable\b",
                     r"\btodo\b", r"\baction\b", r"\bwork\b", r"\bprogress\b",
                     r"\bstatus\b", r"\bupdate\b", r"\bpending\b", r"\bapproval\b"]
        }
        for etype, patterns in keyword_map.items():
            for pat in patterns:
                if re.search(pat, lowered):
                    detected_type = etype
                    break
            if detected_type != "none":
                break
    if detected_type == "none":
        return None

    # Date parsing: dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd
    date_obj = None
    date_patterns = [
        (r"(\d{1,2})/(\d{1,2})/(\d{4})", "%d/%m/%Y"),
        (r"(\d{4})-(\d{1,2})-(\d{1,2})", "%Y-%m-%d"),
    ]
    for pattern, fmt in date_patterns:
        m = re.search(pattern, text)
        if m:
            try:
                date_obj = datetime.strptime(m.group(0), fmt).date()
            except:
                pass
        if date_obj:
            break

    if not date_obj:
        m = re.search(r"(\d{1,2})-(\d{1,2})-(\d{4})", text)
        if m:
            a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
            for d, mth in [(a, b), (b, a)]:
                try:
                    date_obj = datetime(c, mth, d).date()
                    break
                except:
                    continue

    if not date_obj:
        return {"detected_type": detected_type, "title": detected_type.capitalize(),
                "start": None, "duration_minutes": 60, "note": "No date found in email"}

    # Time parsing: hh:mm am/pm or 24h format
    time_obj = None
    m = re.search(r"(\d{1,2}:\d{2})\s*(am|pm)", lowered)
    if m:
        try:
            time_obj = datetime.strptime(m.group(1) + m.group(2), "%I:%M%p").time()
        except:
            pass
    if not time_obj:
        m = re.search(r"(\d{1,2}:\d{2})", lowered)
        if m:
            try:
                time_obj = datetime.strptime(m.group(1), "%H:%M").time()
            except:
                pass

    base_time = time_obj or datetime.strptime("09:00", "%H:%M").time()
    start = datetime.combine(date_obj, base_time).replace(tzinfo=backend_main.IST)

    # Duration: X hour(s) or X min(s)
    duration_minutes = 60
    m = re.search(r"(\d+)\s*(hour|hr|h)", lowered)
    if m:
        duration_minutes = int(m.group(1)) * 60
    else:
        m = re.search(r"(\d+)\s*(min|mins|minute|minutes)", lowered)
        if m:
            duration_minutes = int(m.group(1))

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
        auto_results = []
        for message in messages:
            message_data = gmail.users().messages().get(userId="me", id=message["id"], format="full").execute()
            payload_data = message_data.get("payload", {})
            headers = payload_data.get("headers", [])
            text = _decode_email_body(payload_data) or message_data.get("snippet", "")
            parsed = _parse_email_details(text, backend_main)
            if not parsed:
                continue
            email = {
                "id": message["id"],
                "subject": _email_header(headers, "Subject") or parsed["title"],
                "sender": _email_header(headers, "From"),
                "preview": text[:500],
                **parsed,
            }
            detected_emails.append(email)

            # AUTO-PROCESS: automatically add to Calendar and Notion without asking user
            auto_status = []
            if parsed.get("start"):
                start_time = datetime.fromisoformat(parsed["start"])
                title = parsed["title"]
                intent_type = parsed["detected_type"]
                duration_minutes = parsed.get("duration_minutes", 60)
                try:
                    backend_main.create_calendar_event(title, start_time, intent_type, duration_minutes)
                    auto_status.append("calendar_added")
                except Exception as ce:
                    auto_status.append(f"calendar_skipped: {str(ce)[:50]}")
                try:
                    backend_main.add_to_notion(title, start_time)
                    auto_status.append("notion_added")
                except Exception as ne:
                    auto_status.append(f"notion_skipped: {str(ne)[:50]}")
                email["auto_actions"] = auto_status

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
