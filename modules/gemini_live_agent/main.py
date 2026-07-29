from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from modules.gemini_live_agent.agent import GeminiLiveAgent
from modules.gemini_live_agent.config import get_settings
from modules.gemini_live_agent.routes import build_router


settings = get_settings()
agent = GeminiLiveAgent(settings)
STATIC_DIR = Path(__file__).resolve().parent / "static"


def initialize_module() -> FastAPI:
    """Create the standalone FastAPI service for the Gemini live agent module."""

    app = FastAPI(
        title="GeminiLiveAgentModule",
        version="1.0.0",
        description="Independent multimodal Gemini live-agent service for AgentX and hackathon demos.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if STATIC_DIR.exists():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="gemini-live-agent-assets")
    app.include_router(build_router(agent), prefix="/agentx/live-agent", tags=["Gemini Live Agent"])

    @app.get("/", include_in_schema=False)
    def demo_home() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True, "configured": settings.configured}

    return app


def start_agent_session(metadata: dict | None = None) -> dict:
    """Expose a simple AgentX-friendly session bootstrap API."""

    return agent.start_agent_session(metadata)


app = initialize_module()


if __name__ == "__main__":
    uvicorn.run(
        "modules.gemini_live_agent.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=False,
    )