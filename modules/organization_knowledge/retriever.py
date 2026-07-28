"""
Retriever — performs semantic search to fetch the most relevant document chunks.

High-level flow:
  1. Generate an embedding for the user's query.
  2. Search ChromaDB for similar chunks using cosine distance.
  3. Return the top-k chunks as context for the QA engine.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from modules.organization_knowledge.config import OrganizationKnowledgeSettings, get_settings
from modules.organization_knowledge.embedding_generator import generate_embeddings
from modules.organization_knowledge.vector_store import search_similar, get_collection_count

logger = logging.getLogger("org_knowledge.retriever")


class RetrievalError(Exception):
    """Raised when retrieval fails."""


def retrieve_context(
    query: str,
    top_k: int | None = None,
    settings: OrganizationKnowledgeSettings | None = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve the most relevant document chunks for a given query.

    Args:
        query:    The user's natural language question.
        top_k:    Number of chunks to retrieve (defaults to settings.top_k).
        settings: Optional settings override.

    Returns:
        A list of chunk dicts sorted by relevance (most relevant first).
        Each dict contains:
          - "text":       The chunk content.
          - "score":      Similarity score (lower = more relevant).
          - "metadata":   Dict with document_name, chunk_index, etc.

    Raises:
        RetrievalError: If the retrieval process fails.
        ValueError:     If the query is empty.
    """
    if settings is None:
        settings = get_settings()

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if top_k is None:
        top_k = settings.top_k

    # Step 1: Check if there's any data in the vector store
    doc_count = get_collection_count(settings)
    if doc_count == 0:
        logger.warning("No documents in the knowledge base. Cannot retrieve.")
        return []

    # Step 2: Generate embedding for the query
    try:
        query_embeddings = generate_embeddings([query.strip()], settings)
    except Exception as exc:
        raise RetrievalError(f"Failed to generate query embedding: {exc}")

    if not query_embeddings:
        raise RetrievalError("Query embedding generation returned empty result.")

    query_embedding = query_embeddings[0]

    # Step 3: Search for similar chunks in the vector store
    try:
        results = search_similar(
            query_embedding=query_embedding,
            top_k=top_k,
            settings=settings,
        )
    except Exception as exc:
        raise RetrievalError(f"Vector search failed: {exc}")

    logger.info(
        "Retrieved %d relevant chunks for query (top_k=%d)",
        len(results),
        top_k,
    )
    return results


def is_knowledge_base_initialized(settings: OrganizationKnowledgeSettings | None = None) -> bool:
    """
    Check if the knowledge base has any documents stored.

    Returns:
        True if at least one chunk exists in the vector store.
    """
    if settings is None:
        settings = get_settings()

    count = get_collection_count(settings)
    return count > 0


def get_context_text(
    query: str,
    top_k: int | None = None,
    settings: OrganizationKnowledgeSettings | None = None,
) -> str:
    """
    Retrieve chunks and format them as a single concatenated context string.

    This is a convenience method for the QA engine.

    Args:
        query:    The user's question.
        top_k:    Number of chunks to retrieve.
        settings: Optional settings override.

    Returns:
        A formatted string containing the retrieved document context.
    """
    chunks = retrieve_context(query, top_k, settings)

    if not chunks:
        return ""

    context_parts = []
    for chunk in chunks:
        text = chunk.get("text", "").strip()
        if text:
            context_parts.append(text)

    return "\n\n".join(context_parts)


