"""
Orchestrator — coordinates the entire Organization Knowledge Module workflow.

Provides two main operations:
  1. upload_document(file_path / file_bytes) → processes and stores document.
  2. ask_question(question) → retrieves context and generates an answer.

Also exposes status checks and knowledge base management.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from modules.organization_knowledge.config import OrganizationKnowledgeSettings, get_settings
from modules.organization_knowledge.document_parser import parse_document_bytes
from modules.organization_knowledge.chunk_generator import generate_chunks
from modules.organization_knowledge.embedding_generator import generate_embeddings
from modules.organization_knowledge.vector_store import (
    clear_knowledge_base,
    get_collection_count,
    get_stored_document_names,
    store_document_chunks,
)
from modules.organization_knowledge.retriever import (
    is_knowledge_base_initialized,
    get_context_text,
)
from modules.organization_knowledge.qa_engine import answer_question

logger = logging.getLogger("org_knowledge.orchestrator")


class OrganizationKnowledgeOrchestrator:
    """
    High-level orchestrator for the Organization Knowledge Module.

    Usage:
        orchestrator = OrganizationKnowledgeOrchestrator()

        # Upload a document (replaces previous knowledge base)
        result = orchestrator.upload_document(file_bytes, "company_policy.pdf")

        # Ask a question
        answer = orchestrator.ask_question("What is the dress code?")
    """

    def __init__(self, settings: OrganizationKnowledgeSettings | None = None):
        self.settings = settings or get_settings()
        self._last_document_name: str | None = None
        self._last_upload_time: datetime | None = None

    # ------------------------------------------------------------------
    # Document Upload & Ingestion
    # ------------------------------------------------------------------

    def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> Dict[str, Any]:
        """
        Upload a document, process it, and store it in the vector database.

        This REPLACES any previously stored knowledge base (MVP: single org).

        Args:
            file_bytes: Raw bytes of the uploaded file.
            filename:   Original filename (used for format detection and metadata).

        Returns:
            A dict with:
              - "success":       bool
              - "document_name": The filename
              - "chunks_count":  Number of chunks generated and stored
              - "message":       Human-readable status message
              - "error":         Error message if failed (only when success=False)
        """
        logger.info("Starting upload for '%s' (%d bytes)", filename, len(file_bytes))

        # --- Step 1: Parse the document ---
        try:
            text = parse_document_bytes(file_bytes, filename)
        except Exception as exc:
            logger.error("Document parsing failed: %s", exc)
            return {
                "success": False,
                "document_name": filename,
                "chunks_count": 0,
                "message": "",
                "error": f"Failed to parse document: {exc}",
            }

        if not text.strip():
            return {
                "success": False,
                "document_name": filename,
                "chunks_count": 0,
                "message": "",
                "error": "No text content could be extracted from the document.",
            }

        logger.info(
            "Extracted %d characters from '%s'",
            len(text),
            filename,
        )

        # --- Step 2: Clear previous knowledge base ---
        # MVP: support only ONE organization at a time
        clear_knowledge_base(self.settings)

        # --- Step 3: Generate chunks ---
        try:
            chunks = generate_chunks(text, self.settings)
        except Exception as exc:
            logger.error("Chunk generation failed: %s", exc)
            return {
                "success": False,
                "document_name": filename,
                "chunks_count": 0,
                "message": "",
                "error": f"Failed to generate chunks: {exc}",
            }

        if not chunks:
            return {
                "success": False,
                "document_name": filename,
                "chunks_count": 0,
                "message": "",
                "error": "No chunks were generated from the document.",
            }

        # --- Step 4: Generate embeddings ---
        chunk_texts = [chunk["text"] for chunk in chunks]
        try:
            embeddings = generate_embeddings(chunk_texts, self.settings)
        except Exception as exc:
            logger.error("Embedding generation failed: %s", exc)
            return {
                "success": False,
                "document_name": filename,
                "chunks_count": 0,
                "message": "",
                "error": f"Failed to generate embeddings: {exc}",
            }

        # --- Step 5: Store in vector database ---
        try:
            stored_count = store_document_chunks(
                chunks=chunks,
                embeddings=embeddings,
                document_name=filename,
                settings=self.settings,
            )
        except Exception as exc:
            logger.error("Vector store failed: %s", exc)
            return {
                "success": False,
                "document_name": filename,
                "chunks_count": 0,
                "message": "",
                "error": f"Failed to store embeddings: {exc}",
            }

        # Update internal state
        self._last_document_name = filename
        self._last_upload_time = datetime.now(timezone.utc)

        logger.info(
            "Successfully uploaded '%s': %d chunks stored",
            filename,
            stored_count,
        )

        return {
            "success": True,
            "document_name": filename,
            "chunks_count": stored_count,
            "message": f"Successfully processed '{filename}'. "
                       f"{stored_count} sections indexed and ready for questions.",
            "error": "",
        }

    # ------------------------------------------------------------------
    # Question Answering
    # ------------------------------------------------------------------

    def ask_question(self, question: str) -> Dict[str, Any]:
        """
        Ask a question about the organization's documents.

        Args:
            question: Natural language question from the user.

        Returns:
            A dict with:
              - "success":       bool
              - "answer":        The generated answer text.
              - "found":         Whether the answer was found in the documents.
              - "context_used":  The retrieved chunks used as context.
              - "error":         Error message if failed.
        """
        if not question or not question.strip():
            return {
                "success": False,
                "answer": "",
                "found": False,
                "context_used": [],
                "error": "Question cannot be empty.",
            }

        # Step 1: Check if knowledge base is initialized
        if not is_knowledge_base_initialized(self.settings):
            return {
                "success": False,
                "answer": (
                    "No organization documents have been uploaded yet. "
                    "Please upload a document first."
                ),
                "found": False,
                "context_used": [],
                "error": "",
            }

        # Step 2: Retrieve relevant context
        try:
            context_text = get_context_text(
                query=question,
                top_k=self.settings.top_k,
                settings=self.settings,
            )
        except Exception as exc:
            logger.error("Retrieval failed: %s", exc)
            return {
                "success": False,
                "answer": "",
                "found": False,
                "context_used": [],
                "error": f"Failed to retrieve context: {exc}",
            }

        if not context_text:
            return {
                "success": True,
                "answer": (
                    "I couldn't find any information about this in the "
                    "uploaded organization documents."
                ),
                "found": False,
                "context_used": [],
                "error": "",
            }

        # Step 3: Generate answer from context
        try:
            qa_result = answer_question(
                question=question,
                context=context_text,
                settings=self.settings,
            )
        except Exception as exc:
            logger.error("QA engine failed: %s", exc)
            return {
                "success": False,
                "answer": "",
                "found": False,
                "context_used": [],
                "error": f"Failed to generate answer: {exc}",
            }

        return {
            "success": True,
            "answer": qa_result.get("answer", ""),
            "found": qa_result.get("found", False),
            "context_used": context_text,
            "error": "",
        }

    # ------------------------------------------------------------------
    # Status & Management
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the knowledge base."""
        doc_names = get_stored_document_names(self.settings)
        chunk_count = get_collection_count(self.settings)

        return {
            "has_documents": chunk_count > 0,
            "document_names": doc_names,
            "total_chunks": chunk_count,
            "last_document_name": self._last_document_name,
            "last_upload_time": (
                self._last_upload_time.isoformat() if self._last_upload_time else None
            ),
            "embedding_backend": self.settings.embedding_backend,
            "llm_backend": self.settings.llm_backend,
            "top_k": self.settings.top_k,
        }

    def clear_knowledge_base(self) -> Dict[str, Any]:
        """Clear all stored documents from the knowledge base."""
        cleared = clear_knowledge_base(self.settings)
        self._last_document_name = None
        self._last_upload_time = None

        return {
            "success": cleared,
            "message": "Knowledge base cleared." if cleared else "No knowledge base to clear.",
        }

