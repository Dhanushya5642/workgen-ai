from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GeminiLiveAgentSettings:
    """Runtime settings for the standalone Gemini live agent service."""

    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "")
    location: str = os.getenv("GCP_LOCATION", "us-central1")
    text_model: str = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.0-flash")
    vision_model: str = os.getenv("GEMINI_VISION_MODEL", "gemini-2.0-flash")
    audio_model: str = os.getenv("GEMINI_AUDIO_MODEL", "gemini-2.0-flash")
    tts_enabled: bool = os.getenv("GEMINI_ENABLE_TTS", "false").lower() in {"1", "true", "yes", "on"}
    tts_voice: str = os.getenv("GEMINI_TTS_VOICE", "en-US-Neural2-F")
    default_audio_mime_type: str = os.getenv("GEMINI_AUDIO_MIME_TYPE", "audio/wav")
    default_image_mime_type: str = os.getenv("GEMINI_IMAGE_MIME_TYPE", "image/png")
    service_port: int = int(os.getenv("PORT", "8010"))

    @property
    def configured(self) -> bool:
        return bool(self.google_api_key or self.gcp_project_id)


def get_settings() -> GeminiLiveAgentSettings:
    return GeminiLiveAgentSettings()