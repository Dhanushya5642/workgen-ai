from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from modules.gemini_live_agent.audio_handler import AudioHandler
from modules.gemini_live_agent.config import GeminiLiveAgentSettings
from modules.gemini_live_agent.gemini_client import GeminiClient
from modules.gemini_live_agent.vision_handler import VisionHandler


@dataclass
class AgentSession:
    """In-memory session state for hackathon demos and later AgentX integration."""

    session_id: str
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    turns: list[dict[str, str]] = field(default_factory=list)
    interrupted: bool = False
    last_response: str = ""


class GeminiLiveAgent:
    """Standalone multimodal agent wrapper around Gemini models."""

    def __init__(self, settings: GeminiLiveAgentSettings):
        self.settings = settings
        self.client = GeminiClient(settings)
        self.audio_handler = AudioHandler(settings, self.client)
        self.vision_handler = VisionHandler(settings, self.client)
        self._sessions: dict[str, AgentSession] = {}

    def start_agent_session(self, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        session = AgentSession(
            session_id=str(uuid4()),
            created_at=datetime.now(UTC),
            metadata=metadata or {},
        )
        self._sessions[session.session_id] = session
        return {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "metadata": session.metadata,
        }

    def process_audio_stream(
        self,
        *,
        audio_input: bytes | str,
        prompt: str | None = None,
        mime_type: str | None = None,
        session_id: str | None = None,
        interruption_signal: bool = False,
    ) -> dict[str, Any]:
        session = self._get_or_create_session(session_id)
        audio_bytes = self.audio_handler.resolve_audio_bytes(audio_input)
        transcript = self.audio_handler.transcribe_audio(audio_bytes, mime_type)
        self._add_turn(session, "user", transcript)

        if interruption_signal or self.audio_handler.detect_interruption(transcript):
            return self.handle_interruption(
                session_id=session.session_id,
                reason="Audio interruption detected.",
                user_text=transcript,
            )

        response_text = self.audio_handler.generate_audio_response(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            transcript_hint=transcript,
            prompt=prompt
            or (
                "You are the AgentX Gemini live agent. Listen to the audio request, answer clearly, "
                "and provide a concise next step."
            ),
        )
        self._add_turn(session, "assistant", response_text)
        session.interrupted = False
        session.last_response = response_text

        return self._response_payload(
            session_id=session.session_id,
            text=response_text,
            audio=self.audio_handler.synthesize_speech(response_text),
            visuals=self._build_visuals(
                response_text,
                source="audio",
                extras=[{"type": "transcript", "title": "Recognized speech", "content": transcript}],
            ),
            interrupted=False,
        )

    def process_image(
        self,
        *,
        image_input: bytes | str,
        prompt: str | None = None,
        mime_type: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        session = self._get_or_create_session(session_id)
        user_prompt = prompt or (
            "Analyze this image for a live demo. Explain what you see, the likely intent, and one useful next action."
        )
        analysis = self.vision_handler.analyze_image(
            image_input=image_input,
            prompt=user_prompt,
            mime_type=mime_type,
        )
        self._add_turn(session, "user", user_prompt)
        self._add_turn(session, "assistant", analysis["text"])
        session.interrupted = False
        session.last_response = analysis["text"]

        return self._response_payload(
            session_id=session.session_id,
            text=analysis["text"],
            audio=self.audio_handler.synthesize_speech(analysis["text"]),
            visuals=analysis["visuals"],
            interrupted=False,
        )

    def generate_multimodal_response(
        self,
        *,
        text: str,
        session_id: str | None = None,
        visuals: list[dict[str, Any]] | None = None,
        include_audio: bool = True,
    ) -> dict[str, Any]:
        session = self._get_or_create_session(session_id)
        history = self._history_prompt(session)
        prompt_parts = [
            self.client.text_part(
                "You are AgentX's Gemini live agent. Be conversational, multimodal-aware, and demo friendly."
            ),
        ]
        if history:
            prompt_parts.append(self.client.text_part(history))
        if visuals:
            prompt_parts.append(self.client.text_part(f"Visual context: {json.dumps(visuals)}"))
        prompt_parts.append(self.client.text_part(f"User message: {text}"))

        response_text = self.client.generate_content(model=self.settings.text_model, parts=prompt_parts)
        self._add_turn(session, "user", text)
        self._add_turn(session, "assistant", response_text)
        session.interrupted = False
        session.last_response = response_text

        merged_visuals = visuals or self._build_visuals(response_text, source="text")
        return self._response_payload(
            session_id=session.session_id,
            text=response_text,
            audio=self.audio_handler.synthesize_speech(response_text) if include_audio else "",
            visuals=merged_visuals,
            interrupted=False,
        )

    def handle_interruption(
        self,
        *,
        session_id: str,
        reason: str,
        user_text: str | None = None,
    ) -> dict[str, Any]:
        session = self._get_or_create_session(session_id)
        message = "I have paused the current response so you can redirect me. What should I focus on now?"
        if user_text:
            self._add_turn(session, "user", user_text)
        self._add_turn(session, "assistant", message)
        session.interrupted = True
        session.last_response = message
        return self._response_payload(
            session_id=session.session_id,
            text=message,
            audio=self.audio_handler.synthesize_speech(message),
            visuals=[
                {
                    "type": "interrupt_notice",
                    "title": "Interruption handled",
                    "content": reason,
                }
            ],
            interrupted=True,
        )

    def _get_or_create_session(self, session_id: str | None) -> AgentSession:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]

        started = self.start_agent_session()
        return self._sessions[started["session_id"]]

    def _history_prompt(self, session: AgentSession) -> str:
        if not session.turns:
            return ""
        recent_turns = session.turns[-6:]
        return "\n".join(f"{turn['role']}: {turn['content']}" for turn in recent_turns)

    def _add_turn(self, session: AgentSession, role: str, content: str) -> None:
        session.turns.append({"role": role, "content": content})
        session.turns[:] = session.turns[-10:]

    def _build_visuals(
        self,
        response_text: str,
        *,
        source: str,
        extras: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        bullets = [line.strip("-• ") for line in response_text.splitlines() if line.strip()]
        summary = bullets[0] if bullets else response_text
        visuals = [
            {
                "type": "summary_card",
                "title": f"{source.title()} summary",
                "content": summary[:280],
            }
        ]
        if len(bullets) > 1:
            visuals.append(
                {
                    "type": "next_steps",
                    "title": "Key points",
                    "content": " | ".join(bullets[1:4])[:280],
                }
            )
        if extras:
            visuals.extend(extras)
        return visuals

    def _response_payload(
        self,
        *,
        session_id: str,
        text: str,
        audio: str,
        visuals: list[dict[str, Any]],
        interrupted: bool,
    ) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "text": text,
            "audio": audio,
            "visuals": visuals,
            "interrupted": interrupted,
        }