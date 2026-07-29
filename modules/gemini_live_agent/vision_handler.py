from __future__ import annotations

import base64
import importlib
from typing import Any

from modules.gemini_live_agent.config import GeminiLiveAgentSettings
from modules.gemini_live_agent.gemini_client import GeminiClient


class VisionHandler:
    """Handles uploaded images and optional webcam capture for demos."""

    def __init__(self, settings: GeminiLiveAgentSettings, client: GeminiClient):
        self.settings = settings
        self.client = client

    def resolve_image_bytes(self, image_input: bytes | str) -> bytes:
        if isinstance(image_input, bytes):
            return image_input

        payload = image_input.split(",", 1)[-1].strip()
        if not payload:
            raise ValueError("Image payload is empty.")

        try:
            return base64.b64decode(payload, validate=False)
        except Exception as exc:
            raise ValueError("Image payload must be valid base64 data.") from exc

    def capture_webcam_frame(self, device_index: int = 0) -> tuple[bytes, str]:
        try:
            cv2 = importlib.import_module("cv2")
        except ModuleNotFoundError as exc:
            raise RuntimeError("OpenCV is not installed. Add opencv-python-headless to use webcam capture.") from exc

        camera = cv2.VideoCapture(device_index)
        try:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError("Unable to capture a webcam frame from the selected camera.")

            ok, encoded = cv2.imencode(".png", frame)
            if not ok:
                raise RuntimeError("Unable to encode the webcam frame.")
            return encoded.tobytes(), "image/png"
        finally:
            camera.release()

    def analyze_image(
        self,
        *,
        image_input: bytes | str,
        prompt: str,
        mime_type: str | None = None,
    ) -> dict[str, Any]:
        image_bytes = self.resolve_image_bytes(image_input)
        response_text = self.client.generate_content(
            model=self.settings.vision_model,
            parts=[
                self.client.text_part(prompt),
                self.client.inline_part(image_bytes, mime_type or self.settings.default_image_mime_type),
            ],
        )
        return {
            "text": response_text,
            "visuals": [
                {
                    "type": "image_insight",
                    "title": "Vision reasoning",
                    "content": response_text,
                    "mime_type": mime_type or self.settings.default_image_mime_type,
                }
            ],
        }