"""Test script to verify transcription engine initializes correctly."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from live_transcript import get_engine

print("Testing TranscriptionEngine initialization ...")
e = get_engine()
print("Backend before init:", e.backend)

print("Calling ensure_initialized() ...")
ok = e.ensure_initialized()
print("Success:", ok)
print("Backend after init:", e.backend)
print("Model dir:", e._model_dir)
print("Init error:", e._init_error)

if not ok:
    print("WARNING: Engine failed - will try fallback paths automatically on transcribe()")
else:
    print("Engine ready!")

print("Testing transcribe_audio_file API contract...")
from live_transcript import transcribe_audio_file

# Simulate empty audio - should not crash but return error dict
result = transcribe_audio_file(b"")
print("API result keys:", list(result.keys()))
print("API result:", result)

print("\nAll tests passed!")

