"""
FastAPI Routes for the Organization Knowledge Module.

Provides REST endpoints for:
  - POST /org-knowledge/upload     Upload a document (replaces knowledge base)
  - POST /org-knowledge/ask        Ask a question about the documents
  - GET  /org-knowledge/status     Get knowledge base status
  - POST /org-knowledge/clear      Clear the knowledge base
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile, Form
from pydantic import BaseModel

from modules.organization_knowledge.orchestrator import OrganizationKnowledgeOrchestrator

logger = logging.getLogger("org_knowledge.routes")

# --- Router ---
router = APIRouter(prefix="/org-knowledge", tags=["Organization Knowledge"])

# --- Orchestrator instance (singleton) ---
_orchestrator: OrganizationKnowledgeOrchestrator | None = None


def get_orchestrator() -> OrganizationKnowledgeOrchestrator:
    """Get or create the shared orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrganizationKnowledgeOrchestrator()
    return _orchestrator


# --- Request/Response Models ---


class AskRequest(BaseModel):
    """Request body for asking a question."""
    question: str


class AskResponse(BaseModel):
    """Response from the QA engine."""
    success: bool
    answer: str
    found: bool
    context_used: str = ""
    error: str = ""


class StatusResponse(BaseModel):
    """Knowledge base status."""
    has_documents: bool
    document_names: list[str] = []
    total_chunks: int = 0
    last_document_name: str | None = None
    last_upload_time: str | None = None
    embedding_backend: str = ""
    llm_backend: str = ""
    top_k: int = 5


class UploadResponse(BaseModel):
    """Response after document upload."""
    success: bool
    document_name: str = ""
    chunks_count: int = 0
    message: str = ""
    error: str = ""


class ClearResponse(BaseModel):
    """Response after clearing the knowledge base."""
    success: bool
    message: str = ""


# --- Routes ---


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload an organization document.

    Supported formats: PDF, DOCX, TXT.
    Replaces any previously stored knowledge base.
    """
    orchestrator = get_orchestrator()

    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".txt"}
    ext = ""
    if file.filename:
        ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. "
                   f"Supported formats: {', '.join(allowed_extensions)}",
        )

    # Read file bytes
    try:
        file_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read uploaded file: {exc}",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # Process via orchestrator
    result = orchestrator.upload_document(
        file_bytes=file_bytes,
        filename=file.filename or "document",
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=422,
            detail=result.get("error", "Document processing failed."),
        )

    return UploadResponse(
        success=True,
        document_name=result.get("document_name", ""),
        chunks_count=result.get("chunks_count", 0),
        message=result.get("message", "Document processed successfully."),
    )


@router.post("/ask", response_model=AskResponse)
async def ask_question(payload: AskRequest):
    """
    Ask a question about the uploaded organization documents.

    The answer is strictly based on the document content.
    If the answer is not found, a "not found" message is returned.
    """
    orchestrator = get_orchestrator()

    if not payload.question or not payload.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    result = orchestrator.ask_question(payload.question.strip())

    if not result.get("success") and result.get("error"):
        raise HTTPException(
            status_code=500,
            detail=result["error"],
        )

    return AskResponse(
        success=result.get("success", True),
        answer=result.get("answer", ""),
        found=result.get("found", False),
        context_used=result.get("context_used", ""),
        error=result.get("error", ""),
    )


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get the current status of the organization knowledge base."""
    orchestrator = get_orchestrator()
    status = orchestrator.get_status()

    return StatusResponse(
        has_documents=status.get("has_documents", False),
        document_names=status.get("document_names", []),
        total_chunks=status.get("total_chunks", 0),
        last_document_name=status.get("last_document_name"),
        last_upload_time=status.get("last_upload_time"),
        embedding_backend=status.get("embedding_backend", ""),
        llm_backend=status.get("llm_backend", ""),
        top_k=status.get("top_k", 5),
    )


@router.post("/clear", response_model=ClearResponse)
async def clear_knowledge_base():
    """Clear all stored documents from the knowledge base."""
    orchestrator = get_orchestrator()
    result = orchestrator.clear_knowledge_base()

    return ClearResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
    )

