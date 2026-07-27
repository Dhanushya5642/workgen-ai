import io
import json
import os
import tempfile

try:
    import numpy as np
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    np = None
    WhisperModel = None
    WHISPER_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    AudioSegment = None
    PYDUB_AVAILABLE = False

samplerate = 16000

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
    """Record audio from server microphone (used by CLI mode only)."""
    try:
        import sounddevice as sd
    except ImportError:
        raise RuntimeError("sounddevice is not installed")

    audio = sd.rec(
        int(5 * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    return audio.flatten()


def transcribe_audio_file(audio_bytes: bytes) -> dict:
    """Transcribe audio from raw file bytes (WebM, WAV, etc.) using Whisper.

    This is the function called from the API endpoint when the browser
    sends recorded audio. Returns the same dict shape as before.
    """
    if not WHISPER_AVAILABLE:
        return {
            "transcript": "",
            "segments": [],
            "error": "faster-whisper or numpy not installed",
        }

    model = get_whisper_model()
    if model is None:
        return {
            "transcript": "",
            "segments": [],
            "error": "Failed to load Whisper model",
        }

    # Convert browser audio (WebM / MP4 / etc.) to WAV PCM for Whisper
    try:
        if PYDUB_AVAILABLE:
            seg = AudioSegment.from_file(io.BytesIO(audio_bytes))
            seg = seg.set_frame_rate(samplerate).set_channels(1).set_sample_width(2)
            wav_buf = io.BytesIO()
            seg.export(wav_buf, format="wav")
            wav_buf.seek(0)
            import soundfile as sf
            data, sr = sf.read(wav_buf, dtype="float32")
        else:
            # Fallback without pydub: save to temp file and use soundfile
            import soundfile as sf
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            data, sr = sf.read(tmp_path, dtype="float32")
            os.unlink(tmp_path)
    except Exception as e:
        return {
            "transcript": "",
            "segments": [],
            "error": f"Audio conversion failed: {e}",
        }

    # Transcribe with Whisper
    try:
        segments, _ = model.transcribe(data, language="en")
        lines = [seg.text.strip() for seg in segments if getattr(seg, "text", "").strip()]
        return {
            "transcript": " ".join(lines),
            "segments": [{"text": line} for line in lines],
            "sample_rate": samplerate,
        }
    except Exception as e:
        return {
            "transcript": "",
            "segments": [],
            "error": str(e),
        }


# -------- FUNCTION CALLED FROM MAIN -------- #

def run_live_transcription():
    """CLI-based live transcription using server microphone."""
    if not WHISPER_AVAILABLE:
        print("Live transcription dependencies are not installed. Install faster-whisper, sounddevice, and numpy.")
        return

    model = get_whisper_model()
    if model is None:
        print("Failed to load Whisper model.")
        return

    try:
        import sounddevice as sd
    except ImportError:
        print("sounddevice not installed — cannot run CLI live transcription.")
        return

    print("🎤 Live transcription started")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            audio_data = record_audio()
            segments, info = model.transcribe(audio_data, language="en")
            for segment in segments:
                print(segment.text)
    except KeyboardInterrupt:
        print("\n🛑 Transcription stopped")


# -------- OPTIONAL: RUN DIRECTLY -------- #

if __name__ == "__main__":
    run_live_transcription()

