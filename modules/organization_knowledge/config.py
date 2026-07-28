"""
Configuration for the Organization Knowledge Module.

Reads settings from environment variables with sensible defaults for local development.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class OrganizationKnowledgeSettings:
    """Settings for the Organization Knowledge module."""

    # --- Embedding model ---
    # Options: "ollama" (uses nomic-embed-text or similar) or "openai"
    embedding_backend: str = os.getenv("ORG_KNOWLEDGE_EMBEDDING_BACKEND", "ollama")
    # Ollama embedding model name (used when backend="ollama")
    ollama_embedding_model: str = os.getenv("ORG_KNOWLEDGE_OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    # OpenAI embedding model (used when backend="openai")
    openai_embedding_model: str = os.getenv("ORG_KNOWLEDGE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # --- LLM for QA ---
    # Options: "ollama" or "openai"
    llm_backend: str = os.getenv("ORG_KNOWLEDGE_LLM_BACKEND", "ollama")
    # Ollama model for answering questions
    ollama_llm_model: str = os.getenv("ORG_KNOWLEDGE_OLLAMA_LLM_MODEL", "gemma:2b")
    # OpenAI model for answering questions
    openai_llm_model: str = os.getenv("ORG_KNOWLEDGE_OPENAI_LLM_MODEL", "gpt-4o-mini")

    # --- OpenAI API Key (required if backend is "openai") ---
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # --- Ollama base URL ---
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # --- Chunking ---
    chunk_size: int = int(os.getenv("ORG_KNOWLEDGE_CHUNK_SIZE", "512"))
    chunk_overlap: int = int(os.getenv("ORG_KNOWLEDGE_CHUNK_OVERLAP", "64"))

    # --- Retrieval ---
    top_k: int = int(os.getenv("ORG_KNOWLEDGE_TOP_K", "5"))

    # --- ChromaDB persistence ---
    chroma_db_path: str = os.getenv("ORG_KNOWLEDGE_CHROMA_DB_PATH", "./chroma_db")
    chroma_collection_name: str = os.getenv("ORG_KNOWLEDGE_CHROMA_COLLECTION", "organization_docs")

    # --- Upload ---
    # Maximum upload file size in MB
    max_upload_size_mb: int = int(os.getenv("ORG_KNOWLEDGE_MAX_UPLOAD_MB", "50"))
    # Directory to temporarily store uploaded files during processing
    upload_temp_dir: str = os.getenv("ORG_KNOWLEDGE_TEMP_DIR", "./temp_uploads")


def get_settings() -> OrganizationKnowledgeSettings:
    """Return a frozen settings instance."""
    return OrganizationKnowledgeSettings()

