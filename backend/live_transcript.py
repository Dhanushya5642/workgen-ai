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

model = None


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


# -------- FUNCTION CALLED FROM MAIN -------- #

def run_live_transcription():
    if not WHISPER_AVAILABLE:
        print("Live transcription dependencies are not installed. Install faster-whisper, sounddevice, and numpy.")
        return

    global model
    if model is None:
        model = WhisperModel("tiny", compute_type="int8")

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