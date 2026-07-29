from __future__ import annotations

import base64
import importlib
from typing import Generator

from modules.gemini_live_agent.config import GeminiLiveAgentSettings
from modules.gemini_live_agent.gemini_client import GeminiClient


class AudioHandler:
    """Handles audio decoding, Gemini audio prompts, and optional TTS."""

    INTERRUPTION_KEYWORDS = (
        "stop",
        "pause",
        "wait",
        "hold on",
        "interrupt",
        "one second",
        "actually",
    )

    def __init__(self, settings: GeminiLiveAgentSettings, client: GeminiClient):
        self.settings = settings
        self.client = client

    def resolve_audio_bytes(self, audio_input: bytes | str) -> bytes:
        if isinstance(audio_input, bytes):
            return audio_input

        payload = audio_input.split(",", 1)[-1].strip()
        if not payload:
            raise ValueError("Audio payload is empty.")

        try:
            return base64.b64decode(payload, validate=False)
        except Exception as exc:
            raise ValueError("Audio payload must be valid base64 data.") from exc

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str | None = None) -> str:
        prompt = (
            "Transcribe the user audio accurately. Return only the spoken text, with no extra commentary."
        )
        return self.client.generate_content(
            model=self.settings.audio_model,
            parts=[
                self.client.text_part(prompt),
                self.client.inline_part(audio_bytes, mime_type or self.settings.default_audio_mime_type),
            ],
        )

    def generate_audio_response(
        self,
        *,
        audio_bytes: bytes,
        prompt: str,
        mime_type: str | None = None,
        transcript_hint: str | None = None,
    ) -> str:
        parts = [self.client.text_part(prompt)]
        if transcript_hint:
            parts.append(self.client.text_part(f"Transcript hint: {transcript_hint}"))
        parts.append(self.client.inline_part(audio_bytes, mime_type or self.settings.default_audio_mime_type))
        return self.client.generate_content(model=self.settings.audio_model, parts=parts)

    def detect_interruption(self, transcript: str) -> bool:
        lowered = transcript.lower()
        return any(keyword in lowered for keyword in self.INTERRUPTION_KEYWORDS)

    def synthesize_speech(self, text: str) -> str:
        if not text.strip() or not self.settings.tts_enabled:
            return ""

        try:
            texttospeech = importlib.import_module("google.cloud.texttospeech")
        except ModuleNotFoundError:
            return ""

        try:
            client = texttospeech.TextToSpeechClient()
            language_code = "-".join(self.settings.tts_voice.split("-")[:2]) or "en-US"
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=self.settings.tts_voice,
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
            )
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )
            return base64.b64encode(response.audio_content).decode("utf-8")
        except Exception:
            return ""

    def stream_audio_output(self, text: str, chunk_size: int = 4096) -> Generator[str, None, None]:
        audio_base64 = self.synthesize_speech(text)
        for index in range(0, len(audio_base64), chunk_size):
            yield audio_base64[index : index + chunk_size]