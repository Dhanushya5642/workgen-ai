from __future__ import annotations

import base64
import importlib
from typing import Any

from modules.gemini_live_agent.config import GeminiLiveAgentSettings


class GeminiClientError(RuntimeError):
    """Raised when the Gemini SDK or API call is unavailable."""


class GeminiClient:
    """Thin wrapper around the Google GenAI SDK for plugin-safe usage."""

    def __init__(self, settings: GeminiLiveAgentSettings):
        self.settings = settings
        self._client: Any | None = None

    @staticmethod
    def text_part(text: str) -> dict[str, str]:
        return {"text": text}

    @staticmethod
    def inline_part(data: bytes, mime_type: str) -> dict[str, Any]:
        return {
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(data).decode("utf-8"),
            }
        }

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> Any:
        try:
            genai_module = importlib.import_module("google.genai")
        except ModuleNotFoundError as exc:
            try:
                google_module = importlib.import_module("google")
                genai_module = getattr(google_module, "genai")
            except Exception:
                raise GeminiClientError(
                    "google-genai is not installed. Install modules/gemini_live_agent/requirements.txt first."
                ) from exc

        client_class = getattr(genai_module, "Client", None)
        if client_class is None:
            raise GeminiClientError("Unable to locate google.genai.Client in the installed SDK.")

        if self.settings.google_api_key:
            return client_class(api_key=self.settings.google_api_key)

        if self.settings.gcp_project_id:
            return client_class(
                vertexai=True,
                project=self.settings.gcp_project_id,
                location=self.settings.location,
            )

        raise GeminiClientError("Set GOOGLE_API_KEY or GCP_PROJECT_ID before using GeminiLiveAgent.")

    def generate_content(self, *, model: str, parts: list[dict[str, Any]]) -> str:
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=[{"role": "user", "parts": parts}],
            )
        except GeminiClientError:
            raise
        except Exception as exc:
            raise GeminiClientError(f"Gemini request failed: {exc}") from exc

        text = self._extract_text(response)
        return text or "I understood the request, but Gemini did not return a text response."

    def _extract_text(self, response: Any) -> str | None:
        direct_text = getattr(response, "text", None)
        if isinstance(direct_text, str) and direct_text.strip():
            return direct_text.strip()

        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                text = getattr(part, "text", None)
                if isinstance(text, str) and text.strip():
                    return text.strip()

        return None