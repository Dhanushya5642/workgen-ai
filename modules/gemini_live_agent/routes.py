from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from modules.gemini_live_agent.agent import GeminiLiveAgent
from modules.gemini_live_agent.gemini_client import GeminiClientError


class ChatRequest(BaseModel):
    session_id: str | None = None
    text: str = Field(..., min_length=1, description="User text input for the live agent.")
    visuals: list[dict[str, Any]] = Field(default_factory=list)
    include_audio: bool = True


class MultimodalResponse(BaseModel):
    session_id: str
    text: str
    audio: str = ""
    visuals: list[dict[str, Any]] = Field(default_factory=list)
    interrupted: bool = False


def build_router(agent: GeminiLiveAgent) -> APIRouter:
    router = APIRouter()

    @router.post("/audio", response_model=MultimodalResponse)
    async def audio_endpoint(request: Request) -> MultimodalResponse:
        payload = await _parse_binary_request(request, base64_field="audio_base64")
        audio_input = payload.get("binary_data") or payload.get("base64_data")
        if not audio_input:
            raise HTTPException(status_code=400, detail="Provide audio using multipart file upload or audio_base64.")

        try:
            result = agent.process_audio_stream(
                audio_input=audio_input,
                prompt=payload.get("prompt"),
                mime_type=payload.get("mime_type"),
                session_id=payload.get("session_id"),
                interruption_signal=payload.get("interruption_signal", False),
            )
        except GeminiClientError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return MultimodalResponse(**result)

    @router.post("/image", response_model=MultimodalResponse)
    async def image_endpoint(request: Request) -> MultimodalResponse:
        payload = await _parse_binary_request(request, base64_field="image_base64")
        image_input = payload.get("binary_data") or payload.get("base64_data")

        if payload.get("capture_webcam"):
            try:
                image_input, payload["mime_type"] = agent.vision_handler.capture_webcam_frame()
            except RuntimeError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc

        if not image_input:
            raise HTTPException(
                status_code=400,
                detail="Provide an image using multipart file upload, image_base64, or capture_webcam=true.",
            )

        try:
            result = agent.process_image(
                image_input=image_input,
                prompt=payload.get("prompt"),
                mime_type=payload.get("mime_type"),
                session_id=payload.get("session_id"),
            )
        except GeminiClientError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return MultimodalResponse(**result)

    @router.post("/chat", response_model=MultimodalResponse)
    async def chat_endpoint(request: ChatRequest) -> MultimodalResponse:
        try:
            result = agent.generate_multimodal_response(
                text=request.text,
                session_id=request.session_id,
                visuals=request.visuals,
                include_audio=request.include_audio,
            )
        except GeminiClientError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        return MultimodalResponse(**result)

    return router


async def _parse_binary_request(request: Request, *, base64_field: str) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        file_obj = form.get("file")
        binary_data = await file_obj.read() if hasattr(file_obj, "read") else None
        return {
            "session_id": _clean_optional(form.get("session_id")),
            "prompt": _clean_optional(form.get("prompt")),
            "mime_type": getattr(file_obj, "content_type", None) or _clean_optional(form.get("mime_type")),
            "binary_data": binary_data,
            "base64_data": _clean_optional(form.get(base64_field)),
            "interruption_signal": _as_bool(form.get("interruption_signal")),
            "capture_webcam": _as_bool(form.get("capture_webcam")),
        }

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON or multipart form data.") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object.")

    return {
        "session_id": _clean_optional(payload.get("session_id")),
        "prompt": _clean_optional(payload.get("prompt")),
        "mime_type": _clean_optional(payload.get("mime_type")),
        "binary_data": None,
        "base64_data": _clean_optional(payload.get(base64_field)),
        "interruption_signal": _as_bool(payload.get("interruption_signal")),
        "capture_webcam": _as_bool(payload.get("capture_webcam")),
    }


def _clean_optional(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}