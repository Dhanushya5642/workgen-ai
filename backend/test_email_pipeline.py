from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from backend import api as backend_api
from backend import main as backend_main


def test_decode_email_body_prefers_plain_text_and_falls_back_from_nested_parts():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {
                "mimeType": "text/html",
                "body": {"data": "PGRpdj5NZWV0aW5nIG9uIDExLzA0LzIwMjYgYXQgMTA6MzAgYW08L2Rpdj4="},
            },
            {
                "mimeType": "text/plain",
                "body": {"data": "TWVldGluZyBvbiAxMS8wNC8yMDI2IGF0IDEwOjMwIGFt"},
            },
        ],
    }

    text = backend_api._decode_email_body(payload)

    assert "Meeting on 11/04/2026 at 10:30 am" in text


def test_parse_email_details_uses_subject_and_keyword_fallback_when_classifier_fails():
    fake_backend_main = SimpleNamespace(
        classify_email_type=lambda _text: (_ for _ in ()).throw(RuntimeError("ollama unavailable")),
        IST=timezone.utc,
    )

    parsed = backend_api._parse_email_details(
        "Please join the Google Meet on 11/04/2026 at 10:30 am for 2 hours.",
        fake_backend_main,
        subject="Project Kickoff Meeting",
    )

    assert parsed is not None
    assert parsed["detected_type"] == "meeting"
    assert parsed["title"] == "Project Kickoff Meeting"
    assert parsed["duration_minutes"] == 120
    assert parsed["start"].startswith("2026-04-11T10:30:00")


def test_safe_classify_email_type_uses_fast_heuristic_before_llm_call():
    fake_backend_main = SimpleNamespace(
        classify_email_type=lambda _text: (_ for _ in ()).throw(AssertionError("LLM should not be called")),
    )

    detected = backend_api._safe_classify_email_type(
        "Reminder: Google Meet project sync on 11/04/2026 at 10:30 am.",
        fake_backend_main,
    )

    assert detected == "meeting"


def test_create_calendar_event_returns_partial_when_notion_sync_fails():
    inserted_payload = {}

    class FakeEventsApi:
        def insert(self, calendarId, body):
            inserted_payload["calendarId"] = calendarId
            inserted_payload["body"] = body
            return SimpleNamespace(execute=lambda: {"id": "evt-123"})

    class FakeService:
        def events(self):
            return FakeEventsApi()

    with patch.object(backend_main, "get_credentials", return_value=object()), \
         patch.object(backend_main, "build", return_value=FakeService()), \
         patch.object(backend_main, "event_exists", return_value=False), \
         patch.object(backend_main, "save_event_locally"), \
         patch.object(backend_main, "add_to_notion", side_effect=RuntimeError("Notion offline")):
        result = backend_main.create_calendar_event(
            "Demo Event",
            datetime(2026, 4, 11, 10, 30, tzinfo=backend_main.IST),
            "meeting",
            45,
        )

    assert result["status"] == "partial"
    assert result["created"] is True
    assert result["calendar_event_id"] == "evt-123"
    assert "Notion sync failed" in result["message"]
    assert inserted_payload["body"]["summary"] == "Demo Event"


def test_read_emails_returns_structured_email_records():
    message_payload = {
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Demo Meeting"},
                {"name": "From", "value": "mentor@example.com"},
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": "TWVldGluZyBvbiAxMS8wNC8yMDI2IGF0IDEwOjMwIGFtIGZvciAxIGhvdXI="},
                }
            ],
        },
        "snippet": "Meeting on 11/04/2026 at 10:30 am for 1 hour",
    }

    class FakeMessagesApi:
        def list(self, **_kwargs):
            return SimpleNamespace(execute=lambda: {"messages": [{"id": "msg-1"}]})

        def get(self, **_kwargs):
            return SimpleNamespace(execute=lambda: message_payload)

    class FakeUsersApi:
        def messages(self):
            return FakeMessagesApi()

    class FakeGmailService:
        def users(self):
            return FakeUsersApi()

    with patch.object(backend_main, "get_credentials", return_value=object()), patch.object(
        backend_main, "build", return_value=FakeGmailService()
    ):
        emails = backend_main.read_emails(max_results=1)

    assert len(emails) == 1
    assert emails[0]["subject"] == "Demo Meeting"
    assert emails[0]["sender"] == "mentor@example.com"
    assert emails[0]["detected_type"] == "meeting"
    assert emails[0]["datetime"].startswith("2026-04-11T10:30:00")


def test_scan_emails_returns_clean_response_shape():
    fake_emails = [
        {
            "subject": "Demo Meeting",
            "sender": "mentor@example.com",
            "detected_type": "meeting",
            "preview": "Meeting on 11/04/2026 at 10:30 am",
            "datetime": "2026-04-11T10:30:00+00:00",
        }
    ]

    with patch.object(backend_main, "read_emails", return_value=fake_emails), patch.object(
        backend_api, "_load_json_list", return_value=[]
    ):
        result = backend_api.scan_emails(backend_api.EmailScanRequest(max_results=5))

    assert result == {
        "emails": fake_emails,
        "events": [],
        "scanned_count": 1,
    }