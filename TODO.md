# Live Transcription Fix - TODO

## Step 1: Refactor `backend/live_transcript.py`

- [x] Add `logging` and `huggingface_hub` imports
- [x] Create `TranscriptionEngine` singleton class
- [x] Use local model directory: `backend/models/whisper/tiny`
- [x] Auto-download model via `huggingface_hub.snapshot_download()`
- [x] Detect corrupted/missing `model.bin` and re-download
- [x] Fallback to OpenAI Whisper if Faster-Whisper can't recover
- [x] Preserve all existing function signatures and return formats
- [x] Add detailed logging throughout

## Step 2: Update `backend/api.py`

- [x] Add `from contextlib import asynccontextmanager`
- [x] Add `lifespan` context manager for app startup
- [x] Eagerly initialize transcription engine on startup
- [x] Add startup logging for model status

## Step 3: Test and Verify

- [x] Ensure all imports are available (openai, huggingface_hub)
- [ ] Run the module to verify it compiles without errors
- [ ] Verify return formats match frontend expectations
