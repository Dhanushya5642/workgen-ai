# AgentX

**Your inbox never sleeps. Now, neither does your chief of staff.**

AgentX is a multi-agent AI system built for **Agentverse Hackathon 2026** by **Team Scadoo**. It automates the busywork of a working professional's day — reading emails, scheduling meetings, transcribing calls, summarizing decisions, tracking deadlines, and organizing everything into one place — so you spend less time managing your inbox and more time doing the actual work.

---

## The Problem

Working professionals lose hours every week to manual, repetitive coordination — scanning emails for deadlines, updating calendars by hand, writing meeting notes, chasing follow-ups, and searching old threads for context that's already been discussed once before. AgentX turns that manual loop into an automated one.

---

## The Agent Stack

| # | Agent | What it does |
|---|-------|---------------|
| 01 | **Email Agent** *(core)* | Scans incoming mail for deadlines and action items, adds them to Notion & Google Calendar, and sends timely reminders (e.g. a 10 AM meeting triggers a 9 AM nudge) via WhatsApp/email. |
| 02 | **Live Transcription** | Converts meeting audio into real-time text as the conversation happens. |
| 03 | **Meeting Intelligence** | Summarizes meeting transcripts into clear, actionable notes. |
| 04 | **Research Copilot** | Given a topic, generates a finalized, report-ready writeup. |
| 05 | **Journal AI** | A personal reflection space — tracks emotional check-ins over time and surfaces patterns back to the user. |
| 06 | **Knowledge Hub** | Stores meeting summaries and other agent outputs, with traceability back to their original source. |
| 07 | **Rules Agent** | Answers questions about college/organizational rules and regulations from uploaded documents. |

**Flow:** `Capture → Understand → Organize → Act`
The Email Agent is the entry point; every other agent either feeds it context or consumes what it produces, with Notion acting as the shared "brain" across the system.

---

## Tech Stack

- **Backend:** Django, Django REST Framework, FastAPI
- **Frontend:** `agentx-frontend` (see folder for framework details)
- **AI / LLM:** OpenAI API
- **Integrations:** Notion API, Google API (Calendar), WhatsApp
- **Audio processing:** librosa, soundfile, pydub, sounddevice (for live transcription)
- **Database:** MongoDB (via `djongo` / `pymongo` / `mongoengine`), Redis
- **Task queue:** Celery
- **Other:** python-dotenv, python-docx, reportlab (for document/report generation)

---

## Project Structure

```
workgen-ai/
├── agentx-frontend/     # Frontend application
├── backend/             # Backend services & APIs
├── core/                # Core agent logic
├── modules/             # Individual agent modules
├── requirements.txt     # Python dependencies
└── meeting.wav          # Sample audio for transcription testing
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js (for `agentx-frontend`)
- MongoDB instance
- Redis instance
- API keys: OpenAI, Notion, Google Calendar, WhatsApp (Business API)

### Installation

```bash
# Clone the repo
git clone https://github.com/dhivya-1010/workgen-ai.git
cd workgen-ai

# Set up Python environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up frontend
cd agentx-frontend
npm install
```

### Running the app

```bash
# Backend
cd backend
python manage.py runserver

# Frontend (separate terminal)
cd agentx-frontend
npm run dev
```

---

## Team

Built by **Team Scadoo** — III CSE A, Sri Eshwar College of Engineering

- **Dhivya V**
- **Dhanushya T**

---

## Hackathon

Built for **Agentverse Hackathon 2026**.

---
