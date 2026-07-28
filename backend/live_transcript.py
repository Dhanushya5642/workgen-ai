"""
Live Transcription Module

Provides real-time audio transcription using Faster-Whisper with:
- Singleton model (loaded once, reused for all requests)
- Local model directory (backend/models/whisper/) instead of HF cache
- Auto-download and corruption detection/recovery
- Fallback to OpenAI Whisper if Faster-Whisper is unrecoverable
- Detailed logging and exception handling
"""

import io
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger("live_transcript")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# ---------------------------------------------------------------------------
# Conditional imports
# ---------------------------------------------------------------------------

try:
    import numpy as np
    from faster_whisper import WhisperModel

    FASTER_WHISPER_AVAILABLE = True
    logger.info("faster-whisper is available")
except ImportError as e:
    np = None
    WhisperModel = None
    FASTER_WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed (%s)", e)

try:
    from pydub import AudioSegment

    PYDUB_AVAILABLE = True
except ImportError:
    AudioSegment = None
    PYDUB_AVAILABLE = False

try:
    import soundfile as sf

    SOUNDFILE_AVAILABLE = True
except ImportError:
    sf = None
    SOUNDFILE_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

samplerate = 16000

# Local model directory — inside the project, NOT huggingface cache
MODELS_DIR = Path(__file__).resolve().parent / "models" / "whisper"
MODEL_SIZE = "tiny"
MODEL_SUBDIR = MODELS_DIR / MODEL_SIZE

# HF repo for the given model size
HF_REPO_IDS = {
    "tiny": "Systran/faster-whisper-tiny",
    "base": "Systran/faster-whisper-base",
    "small": "Systran/faster-whisper-small",
    "medium": "Systran/faster-whisper-medium",
    "large": "Systran/faster-whisper-large-v3",
}


# ---------------------------------------------------------------------------
# Model corruption / health helpers
# ---------------------------------------------------------------------------


def _model_bin_path(model_dir: Path) -> Path:
    """Return the expected path to model.bin inside a local model directory."""
    return model_dir / "model.bin"


def _is_model_healthy(model_dir: Path) -> bool:
    """Check whether model.bin exists and has reasonable size (> 10 MB)."""
    bin_path = _model_bin_path(model_dir)
    if not bin_path.exists():
        logger.warning("model.bin not found at %s", bin_path)
        return False
    size_mb = bin_path.stat().st_size / (1024 * 1024)
    if size_mb < 10:
        logger.warning(
            "model.bin at %s is too small (%.1f MB) — corrupt download",
            bin_path,
            size_mb,
        )
        return False
    logger.info("model.bin at %s is healthy (%.1f MB)", bin_path, size_mb)
    return True


# ---------------------------------------------------------------------------
# Model download helper
# ---------------------------------------------------------------------------


def _download_model(model_size: str = MODEL_SIZE) -> Path:
    """Download the Faster-Whisper model to the local project directory.

    Uses huggingface_hub.snapshot_download() to get a consistent snapshot.
    Returns the local path to the model directory.
    """
    repo_id = HF_REPO_IDS.get(model_size)
    if repo_id is None:
        raise ValueError(
            f"Unknown model size '{model_size}'. "
            f"Choose from {list(HF_REPO_IDS.keys())}"
        )

    local_dir = MODELS_DIR / model_size
    local_dir.mkdir(parents=True, exist_ok=True)

    try:
        from huggingface_hub import snapshot_download

        logger.info(
            "Downloading model %s to %s (this may take a while) …",
            repo_id,
            local_dir,
        )
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            resume_download=True,
            ignore_patterns=["*.h5", "*.ot", "*.msgpack"],
        )
        logger.info("Model download complete at %s", local_dir)
    except Exception as exc:
        logger.error("Failed to download model %s: %s", repo_id, exc)
        raise

    return local_dir


def _ensure_model_downloaded(model_size: str = MODEL_SIZE) -> Path:
    """Return the local model path, downloading (or re-downloading) if needed.

    If the local directory exists but model.bin is missing / corrupt, the
    directory is wiped and re-downloaded automatically.
    """
    local_dir = MODELS_DIR / model_size

    # ── Fast path: healthy model exists ──────────────────────────────
    if _is_model_healthy(local_dir):
        logger.info("Using existing local model at %s", local_dir)
        return local_dir

    # ── Corrupt / missing → clean & re-download ──────────────────────
    if local_dir.exists():
        logger.warning(
            "Model at %s is missing or corrupt. Re-downloading …", local_dir
        )
        import shutil

        shutil.rmtree(local_dir)

    return _download_model(model_size)


# ===================================================================
# TranscriptionEngine — Singleton
# ===================================================================


class TranscriptionEngine:
    """Singleton that owns the Whisper model instance.

    Responsibilities:
      - Load Faster-Whisper once at startup (or lazily on first call)
      - Detect corruption and auto-recover by re-downloading
      - Fall back to OpenAI Whisper if Faster-Whisper is unrecoverable
      - Provide a ``transcribe()`` method that returns the standard dict
    """

    def __init__(self):
        self._model = None
        self._fallback_model = None  # OpenAI Whisper model (if used)
        self._backend = None  # "faster-whisper" or "openai-whisper"
        self._model_dir = None
        self._initialized = False
        self._init_error = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def backend(self) -> str:
        return self._backend or "none"

    def ensure_initialized(self) -> bool:
        """Try to initialize (or re-initialize) the model.

        Returns True if the model is usable, False otherwise.
        """
        if self._model is not None:
            return True

        try:
            self._init_faster_whisper()
            return True
        except Exception as exc:
            logger.warning(
                "Faster-Whisper init failed: %s. Trying OpenAI Whisper fallback …",
                exc,
            )

        try:
            self._init_openai_whisper()
            return True
        except Exception as exc:
            logger.error("OpenAI Whisper fallback also failed: %s", exc)
            self._init_error = str(exc)
            return False

    def transcribe(self, audio_data, language: str = "en") -> dict:
        """Transcribe a float32 numpy array.

        Returns the standard dict with keys:
          transcript, segments, sample_rate
        or on error:
          transcript, segments, error
        """
        if not self.ensure_initialized():
            return {
                "transcript": "",
                "segments": [],
                "error": self._init_error or "No transcription backend available",
            }

        if self._backend == "faster-whisper":
            return self._transcribe_faster(audio_data, language)
        else:
            return self._transcribe_openai(audio_data, language)

    # ------------------------------------------------------------------
    # Faster-Whisper
    # ------------------------------------------------------------------

    def _init_faster_whisper(self):
        """Initialize Faster-Whisper model from local directory."""
        if not FASTER_WHISPER_AVAILABLE:
            raise RuntimeError("faster-whisper package not installed")

        model_size = MODEL_SIZE
        logger.info("Initializing Faster-Whisper (%s) …", model_size)

        # Download / verify local model
        local_dir = _ensure_model_downloaded(model_size)
        self._model_dir = local_dir

        logger.info("Loading WhisperModel from %s …", local_dir)
        self._model = WhisperModel(
            str(local_dir),
            compute_type="int8",
            local_files_only=True,
        )
        self._backend = "faster-whisper"
        logger.info("Faster-Whisper model loaded successfully")

    def _transcribe_faster(self, audio_data, language: str) -> dict:
        """Transcribe using Faster-Whisper."""
        try:
            segments, info = self._model.transcribe(audio_data, language=language)
            lines = [seg.text.strip() for seg in segments if seg.text.strip()]
            return {
                "transcript": " ".join(lines),
                "segments": [{"text": line} for line in lines],
                "sample_rate": samplerate,
            }
        except Exception as exc:
            logger.error("Faster-Whisper transcription failed: %s", exc)
            return {
                "transcript": "",
                "segments": [],
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # OpenAI Whisper (fallback)
    # ------------------------------------------------------------------

    def _init_openai_whisper(self):
        """Initialize OpenAI Whisper as a fallback backend."""
        logger.info("Attempting to load OpenAI Whisper (fallback) …")

        try:
            import whisper
        except ImportError:
            raise RuntimeError(
                "openai-whisper is not installed. "
                "Install it with: pip install openai-whisper"
            )

        model_size = MODEL_SIZE
        logger.info("Loading openai-whisper model '%s' …", model_size)
        self._fallback_model = whisper.load_model(model_size)
        self._backend = "openai-whisper"
        logger.info("OpenAI Whisper fallback loaded successfully")

    def _transcribe_openai(self, audio_data, language: str) -> dict:
        """Transcribe using OpenAI Whisper (local fallback)."""
        try:
            import whisper
        except ImportError:
            return {
                "transcript": "",
                "segments": [],
                "error": "openai-whisper not installed for fallback",
            }

        try:
            result = self._fallback_model.transcribe(
                audio_data, language=language, fp16=False
            )
            segments_list = result.get("segments", [])
            lines = [seg["text"].strip() for seg in segments_list if seg["text"].strip()]
            return {
                "transcript": " ".join(lines),
                "segments": [{"text": line} for line in lines],
                "sample_rate": samplerate,
            }
        except Exception as exc:
            logger.error("OpenAI Whisper transcription failed: %s", exc)
            return {
                "transcript": "",
                "segments": [],
                "error": str(exc),
            }


# ===================================================================
# Singleton instance
# ===================================================================

_engine = TranscriptionEngine()


# ===================================================================
# Public helpers (preserved from original API)
# ===================================================================


def get_whisper_model():
    """Return the underlying Whisper model instance (backwards compat).

    Used only by the CLI ``run_live_transcription()`` path.
    """
    _engine.ensure_initialized()
    if _engine._backend == "faster-whisper":
        return _engine._model
    return None


def get_engine() -> TranscriptionEngine:
    """Return the singleton TranscriptionEngine (used by api.py lifespan)."""
    return _engine


# ------------------------------------------------------------------
# Audio recording (CLI-only)
# ------------------------------------------------------------------


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
        dtype="float32",
    )
    sd.wait()
    return audio.flatten()


# ------------------------------------------------------------------
# Audio conversion
# ------------------------------------------------------------------


def _check_ffmpeg():
    """Check if ffmpeg is available on the system."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
            timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def _convert_with_pydub(audio_bytes):
    """Convert audio bytes to float array using pydub."""
    seg = AudioSegment.from_file(io.BytesIO(audio_bytes))
    seg = seg.set_frame_rate(samplerate).set_channels(1).set_sample_width(2)
    wav_buf = io.BytesIO()
    seg.export(wav_buf, format="wav")
    wav_buf.seek(0)
    data, sr = sf.read(wav_buf, dtype="float32")
    return data, sr


def _convert_with_ffmpeg(audio_bytes):
    """Convert audio bytes to float array using direct ffmpeg subprocess."""
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_in:
        tmp_in.write(audio_bytes)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path + ".wav"

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                tmp_in_path,
                "-ar",
                str(samplerate),
                "-ac",
                "1",
                "-sample_fmt",
                "s16",
                tmp_out_path,
            ],
            capture_output=True,
            check=True,
            timeout=30,
        )
        data, sr = sf.read(tmp_out_path, dtype="float32")
        return data, sr
    finally:
        for p in [tmp_in_path, tmp_out_path]:
            if os.path.exists(p):
                os.unlink(p)


def _convert_with_tempfile(audio_bytes):
    """Fallback: write to temp file and try soundfile directly."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        data, sr = sf.read(tmp_path, dtype="float32")
        return data, sr
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def convert_audio_to_float32(audio_bytes: bytes):
    """Convert audio bytes (WebM/WAV/etc.) to float32 numpy array.

    Tries multiple strategies in order:
    1. pydub (requires ffmpeg installed on system)
    2. Direct ffmpeg subprocess call
    3. Temp file fallback (only works if already WAV format)
    """
    # Strategy 1: pydub
    if PYDUB_AVAILABLE and SOUNDFILE_AVAILABLE:
        try:
            return _convert_with_pydub(audio_bytes)
        except Exception as e:
            logger.debug("pydub conversion failed: %s", e)
    elif not SOUNDFILE_AVAILABLE:
        logger.warning("soundfile not installed — skipping pydub strategy")

    # Strategy 2: direct ffmpeg
    if _check_ffmpeg() and SOUNDFILE_AVAILABLE:
        try:
            return _convert_with_ffmpeg(audio_bytes)
        except Exception as e:
            logger.debug("ffmpeg subprocess conversion failed: %s", e)

    # Strategy 3: temp file fallback
    if SOUNDFILE_AVAILABLE:
        try:
            return _convert_with_tempfile(audio_bytes)
        except Exception as e:
            logger.debug("tempfile fallback conversion failed: %s", e)
            raise RuntimeError(
                f"All audio conversion methods failed. Last error: {e}"
            )
    else:
        raise RuntimeError(
            "No audio conversion method available — install pydub + ffmpeg or soundfile"
        )


# ===================================================================
# Main transcription API (called from api.py)
# ===================================================================


def transcribe_audio_file(audio_bytes: bytes) -> dict:
    """Transcribe audio from raw file bytes (WebM, WAV, etc.) using Whisper.

    This is the function called from the API endpoint when the browser
    sends recorded audio. Returns the same dict shape as before.
    """
    # Convert browser audio (WebM / MP4 / etc.) to WAV PCM for Whisper
    try:
        data, sr = convert_audio_to_float32(audio_bytes)
    except Exception as e:
        logger.error("Audio conversion failed: %s", e)
        return {
            "transcript": "",
            "segments": [],
            "error": f"Audio conversion failed: {e}",
        }

    # Check if we got valid audio data
    if data is None or len(data) == 0:
        logger.warning("Decoded audio is empty")
        return {
            "transcript": "",
            "segments": [],
            "error": "Decoded audio is empty",
        }

    # Transcribe with the engine (handles Faster-Whisper or fallback)
    return _engine.transcribe(data, language="en")


# ===================================================================
# CLI mode
# ===================================================================


def run_live_transcription():
    """CLI-based live transcription using server microphone."""
    if not FASTER_WHISPER_AVAILABLE:
        print(
            "Live transcription dependencies are not installed. "
            "Install faster-whisper, sounddevice, and numpy."
        )
        return

    if not _engine.ensure_initialized():
        print("Failed to load any transcription model.")
        return

    try:
        import sounddevice as sd
    except ImportError:
        print("sounddevice not installed — cannot run CLI live transcription.")
        return

    print(f"🎤 Live transcription started (backend: {_engine.backend})")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            audio_data = record_audio()
            result = _engine.transcribe(audio_data, language="en")
            if result.get("transcript"):
                print(result["transcript"])
    except KeyboardInterrupt:
        print("\n🛑 Transcription stopped")


# ===================================================================
# Direct execution
# ===================================================================

if __name__ == "__main__":
    run_live_transcription()

