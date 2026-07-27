from __future__ import print_function

from win10toast import ToastNotifier
from twilio.rest import Client

import os
import base64
import json
import ollama
import time
import re

from notion_client import Client as NotionClient
from dotenv import load_dotenv

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from datetime import datetime, timedelta, timezone

# ---------------- CORE MODULES ---------------- #

from meeting_summarizer import summarize_meeting
from knowledge_hub import store_meeting

# ---------------- ADDITIONAL MODULES (SAFE IMPORT) ---------------- #

try:
    from research_engine import run_research_engine
except:
    run_research_engine = None

try:
    from journal_ai import run_journal_ai
except:
    run_journal_ai = None

try:
    from meeting_pipeline import run_meeting_pipeline
except:
    run_meeting_pipeline = None

try:
    from live_transcript import run_live_transcription
except:
    run_live_transcription = None

try:
    from dashboard import run_dashboard
except:
    run_dashboard = None


# ---------------- CONFIG ---------------- #

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_MEETING_TOKEN")
NOTION_DATABASE_ID = "31461e925a9480d29a9fefc14d9ac655"

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_TO = os.getenv("TWILIO_WHATSAPP_TO")

notion = NotionClient(auth=NOTION_TOKEN) if NOTION_TOKEN else None

IST = timezone(timedelta(hours=5, minutes=30))

toaster = ToastNotifier()

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar'
]


# ---------------- WHATSAPP ---------------- #

def send_whatsapp_message(text):

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_WHATSAPP_TO:
        print("⚠ Twilio credentials missing")
        return

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        message = client.messages.create(
            from_='whatsapp:+14155238886',
            body=text,
            to=TWILIO_WHATSAPP_TO
        )

        print("📲 WhatsApp sent:", message.sid)

    except Exception as e:
        print("WhatsApp Error:", e)


# ---------------- AUTH ---------------- #

def get_credentials():

    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)

            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


# ---------------- AI CLASSIFIER ---------------- #

def classify_email_type(email_text):

    prompt = f"""
Classify this email into ONE of:
meeting, exam, task, interview, payment, none.

Return ONLY JSON:
{{ "type": "" }}

Email:
{email_text}
"""

    response = ollama.chat(
        model="gemma:2b",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )

    try:
        return json.loads(response["message"]["content"]).get("type", "none")
    except:
        return "none"


# ---------------- MARK EMAIL READ ---------------- #

def mark_email_read(gmail, message_id):

    gmail.users().messages().modify(
        userId='me',
        id=message_id,
        body={'removeLabelIds': ['UNREAD']}
    ).execute()


# ---------------- DUPLICATE CHECK ---------------- #

def event_exists(service, title, start_time):

    events = service.events().list(
        calendarId='primary',
        timeMin=start_time.isoformat(),
        timeMax=(start_time + timedelta(minutes=1)).isoformat(),
        singleEvents=True
    ).execute()

    for event in events.get('items', []):
        if event.get('summary') == title:
            return True

    return False


# ---------------- LOCAL STORAGE ---------------- #

def save_event_locally(title, start_time):

    event_data = {
        "title": title,
        "datetime": start_time.isoformat(),
        "reminded": False
    }

    if os.path.exists("events.json"):
        with open("events.json", "r") as f:
            events = json.load(f)
    else:
        events = []

    events.append(event_data)

    with open("events.json", "w") as f:
        json.dump(events, f, indent=2)


# ---------------- NOTION ---------------- #

def add_to_notion(title, start_time):

    if not notion:
        return

    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Date": {"date": {"start": start_time.isoformat()}},
                "Status": {"select": {"name": "Pending"}},
                "Source": {"rich_text": [{"text": {"content": "Created by AgentX"}}]}
            }
        )

        print("📝 Added to Notion")

    except Exception as e:
        print("Notion Error:", e)


# ---------------- CALENDAR ---------------- #

def create_calendar_event(title, start_time, intent_type, duration_minutes):

    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    if event_exists(service, title, start_time):
        print("⚠ Duplicate event skipped")
        return

    end_time = start_time + timedelta(minutes=duration_minutes)

    event = {
        'summary': title,
        'description': f"Created by AgentX ({intent_type})",
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Kolkata'}
    }

    service.events().insert(calendarId='primary', body=event).execute()

    print("🎨 Added to Google Calendar")

    save_event_locally(title, start_time)
    add_to_notion(title, start_time)


# ---------------- EMAIL PROCESSOR ---------------- #

def process_email(original_text, gmail, message_id):

    text_lower = original_text.lower()

    detected_type = classify_email_type(original_text)

    if "exam" in text_lower:
        detected_type = "exam"
    elif "meeting" in text_lower:
        detected_type = "meeting"

    if detected_type == "none":
        mark_email_read(gmail, message_id)
        return

    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', original_text)

    if not date_match:
        mark_email_read(gmail, message_id)
        return

    date_obj = datetime.strptime(date_match.group(1), "%d/%m/%Y")

    time_match = re.search(r'(\d{1,2}:\d{2}\s*(am|pm))', text_lower)

    if time_match:
        time_obj = datetime.strptime(time_match.group(1), "%I:%M %p").time()
    else:
        time_obj = datetime.strptime("09:00", "%H:%M").time()

    dt = datetime.combine(date_obj.date(), time_obj).replace(tzinfo=IST)

    duration_minutes = 60

    title = detected_type.capitalize()

    print(f"🔥 Detected {detected_type} → {title}")

    create_calendar_event(title, dt, detected_type, duration_minutes)

    mark_email_read(gmail, message_id)


# ---------------- EMAIL READER ---------------- #

def read_emails():

    creds = get_credentials()
    gmail = build('gmail', 'v1', credentials=creds)

    results = gmail.users().messages().list(
        userId='me',
        labelIds=['UNREAD'],
        maxResults=5
    ).execute()

    messages = results.get('messages', [])

    print("Unread found:", len(messages))

    for msg in messages:

        msg_data = gmail.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        parts = msg_data['payload'].get('parts', [])

        for part in parts:

            if part['mimeType'] == 'text/plain':

                text = base64.urlsafe_b64decode(
                    part['body']['data']
                ).decode()

                print("\nEMAIL:\n", text)

                process_email(text, gmail, msg['id'])


# ---------------- REMINDER ---------------- #

def check_reminders():

    if not os.path.exists("events.json"):
        return

    with open("events.json", "r") as f:
        events = json.load(f)

    now = datetime.now(IST)

    for event in events:

        event_time = datetime.fromisoformat(event["datetime"])
        reminder_time = event_time - timedelta(hours=1)

        if not event["reminded"] and reminder_time <= now < event_time:

            toaster.show_toast(
                "🔔 AgentX Reminder",
                f"{event['title']} at {event_time.strftime('%H:%M')}",
                duration=10,
                threaded=True
            )

            send_whatsapp_message(event['title'])

            event["reminded"] = True

    with open("events.json", "w") as f:
        json.dump(events, f, indent=2)


# ---------------- MEETING SUMMARIZER ---------------- #

# For UI
def run_meeting_summarizer(transcript):
    result = summarize_meeting(transcript)
    store_meeting(result)
    return result


# For terminal
def run_meeting_summarizer_cli():
    transcript = input("Enter meeting transcript:\n")
    result = run_meeting_summarizer(transcript)
    print(result)


# ---------------- LOOP ---------------- #

def automation_loop():

    print("🤖 AgentX Running...\n")

    while True:
        read_emails()
        check_reminders()
        print("Cycle done...\n")
        time.sleep(300)


# ---------------- MAIN MENU ---------------- #

def main_menu():

    while True:

        print("""
AgentX System

1 → Email Automation
2 → Meeting Summarizer
3 → Research Copilot
4 → Journal AI
5 → Meeting Pipeline
6 → Live Transcription
7 → Dashboard
8 → Exit
""")

        choice = input("Select option: ")

        if choice == "1":
            automation_loop()

        elif choice == "2":
            run_meeting_summarizer()

        elif choice == "3" and run_research_engine:
            run_research_engine()

        elif choice == "4" and run_journal_ai:
            run_journal_ai()

        elif choice == "5" and run_meeting_pipeline:
            run_meeting_pipeline()

        elif choice == "6" and run_live_transcription:
            run_live_transcription()

        elif choice == "7" and run_dashboard:
            run_dashboard()

        elif choice == "8":
            print("Exiting AgentX...")
            break

        else:
            print("⚠ Module not available")


# ---------------- START ---------------- #

if __name__ == "__main__":
    main_menu()