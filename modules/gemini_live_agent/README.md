# GeminiLiveAgentModule

GeminiLiveAgentModule is a standalone multimodal FastAPI service for the AgentX hackathon demo. It is intentionally isolated from the existing `backend/` runtime so it can run as a plugin today and integrate with AgentX later through a clean interface. It also ships with its own demo website served directly by the module.

## What it does

- accepts text, image, and audio interactions
- uses Gemini models through the Google GenAI SDK
- supports interruption-aware voice flows
- returns multimodal payloads in the shape:
  - `text`
  - `audio`
  - `visuals`

## Folder layout

- `main.py` - standalone FastAPI entrypoint
- `agent.py` - `GeminiLiveAgent` orchestration and session state
- `audio_handler.py` - audio decoding, speech-to-text prompting, optional TTS, interruption handling
- `vision_handler.py` - uploaded image reasoning and optional webcam capture helper
- `gemini_client.py` - lightweight Google GenAI SDK wrapper
- `routes.py` - FastAPI routes for `/audio`, `/image`, and `/chat`
- `config.py` - environment-driven runtime configuration
- `static/` - standalone demo website assets served by FastAPI

## AgentX integration points

The module exposes two compatibility functions:

- `initialize_module()` → returns the FastAPI app
- `start_agent_session()` → creates an isolated session for a future AgentX orchestrator

Because the service is contained in `modules/gemini_live_agent`, it does not require changes to existing AgentX core or backend files.

## Environment variables

- `GOOGLE_API_KEY` - easiest option for direct Gemini API access
- `GCP_PROJECT_ID` - use when running with Vertex AI credentials
- `GCP_LOCATION` - defaults to `us-central1`
- `GEMINI_TEXT_MODEL` - defaults to `gemini-2.0-flash`
- `GEMINI_VISION_MODEL` - defaults to `gemini-2.0-flash`
- `GEMINI_AUDIO_MODEL` - defaults to `gemini-2.0-flash`
- `GEMINI_ENABLE_TTS` - set to `true` to enable Google Cloud Text-to-Speech output
- `GEMINI_TTS_VOICE` - defaults to `en-US-Neural2-F`
- `PORT` - FastAPI service port, default `8010`

## Run locally

1. install dependencies from `modules/gemini_live_agent/requirements.txt`
2. set `GOOGLE_API_KEY` or `GCP_PROJECT_ID`
3. start the service:
   - `python -m modules.gemini_live_agent.main`

The service starts independently from the existing AgentX backend.

Then open:

- `http://127.0.0.1:8010/` for the demo website
- `http://127.0.0.1:8010/docs` for Swagger API docs

## API endpoints

- `POST /agentx/live-agent/chat`
  - JSON body with `text`, optional `session_id`, optional `visuals`
- `POST /agentx/live-agent/audio`
  - accepts JSON with `audio_base64` or multipart upload field `file`
- `POST /agentx/live-agent/image`
  - accepts JSON with `image_base64`, multipart upload field `file`, or `capture_webcam=true`

Example chat payload:

```json
{
  "text": "Explain the chart on my dashboard and tell me what to do next.",
  "include_audio": true
}
```

## Deployment on Google Cloud

### Cloud Run

- package the module as a lightweight service
- set environment variables such as `GOOGLE_API_KEY`, `GEMINI_ENABLE_TTS`, and `PORT`
- deploy with a command similar to:
  - `gcloud run deploy gemini-live-agent --source . --region us-central1 --set-env-vars GOOGLE_API_KEY=YOUR_KEY`

### Vertex AI

- configure application default credentials or workload identity
- set `GCP_PROJECT_ID` and `GCP_LOCATION`
- omit `GOOGLE_API_KEY` if using Vertex AI authenticated access

## Demo tips

- enable TTS for a more convincing hackathon demo
- use `/image` for document reading, UI walkthroughs, and homework explanations
- use `/audio` to demonstrate hands-free voice interaction and interruption handling
- use the built-in website at `/` for a cleaner hackathon demo than Swagger alone

## Notes

- if TTS is disabled or unavailable, the module still returns `text` and `visuals`; the `audio` field will be empty
- webcam capture depends on `opencv-python-headless` and local camera access
