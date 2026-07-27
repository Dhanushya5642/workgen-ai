import json
import os

try:
    import sounddevice as sd
    import numpy as np
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    sd = None
    np = None
    WhisperModel = None
    WHISPER_AVAILABLE = False

samplerate = 16000
duration = 5

_model_instance = None


def get_whisper_model():
    global _model_instance
    if _model_instance is None and WhisperModel is not None:
        try:
            _model_instance = WhisperModel("tiny", compute_type="int8")
        except Exception as e:
            print(f"Failed to load Whisper model: {e}")
    return _model_instance


def record_audio():
    if not sd:
        raise RuntimeError("sounddevice is not installed")

    audio = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="float32"
    )

    sd.wait()

    return audio.flatten()


def transcribe_audio():
    """Safe transcription function that returns dict for API endpoints."""
    if not WHISPER_AVAILABLE:
        return {
            "transcript": "",
            "segments": [],
            "error": "faster-whisper, sounddevice, or numpy not installed"
        }

    model = get_whisper_model()
    if model is None:
        return {
            "transcript": "",
            "segments": [],
            "error": "Failed to load Whisper model"
        }

    try:
        audio_data = record_audio()
        segments, _ = model.transcribe(audio_data, language="en")
        lines = [segment.text.strip() for segment in segments if getattr(segment, "text", "").strip()]
        return {
            "transcript": " ".join(lines),
            "segments": [{"text": line} for line in lines],
            "duration": duration,
            "sample_rate": samplerate,
        }
    except Exception as e:
        return {
            "transcript": "",
            "segments": [],
            "error": str(e)
        }


# -------- FUNCTION CALLED FROM MAIN -------- #

def run_live_transcription():
    if not WHISPER_AVAILABLE:
        print("Live transcription dependencies are not installed. Install faster-whisper, sounddevice, and numpy.")
        return

    model = get_whisper_model()
    if model is None:
        print("Failed to load Whisper model.")
        return

    print("🎤 Live transcription started")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            audio_data = record_audio()

            segments, info = model.transcribe(
                audio_data,
                language="en"
            )

            for segment in segments:
                print(segment.text)

    except KeyboardInterrupt:
        print("\n🛑 Transcription stopped")


# -------- OPTIONAL: RUN DIRECTLY -------- #

if __name__ == "__main__":
    run_live_transcription()

