"""
Vector Database — ChromaDB wrapper for persisting and querying document embeddings.

Provides:
  - store_document_chunks:  Ingest chunk texts + embeddings into ChromaDB.
  - search_similar:        Find the most relevant chunks for a query embedding.
  - clear_knowledge_base:   Delete all stored vectors (for document replacement).
"""

from __future__ import annotations

import logging
import os
import shutil
from typing import Any, Dict, List, Optional
from uuid import uuid4

from modules.organization_knowledge.config import OrganizationKnowledgeSettings, get_settings

logger = logging.getLogger("org_knowledge.vector_store")


class VectorStoreError(Exception):
    """Raised when vector store operations fail."""


def get_chroma_client(settings: OrganizationKnowledgeSettings | None = None):
    """Get or create the ChromaDB persistent client."""
    if settings is None:
        settings = get_settings()

    try:
        import chromadb
    except ImportError:
        raise VectorStoreError(
            "chromadb is not installed. Run: pip install chromadb"
        )

    db_path = settings.chroma_db_path
    os.makedirs(db_path, exist_ok=True)

    client = chromadb.PersistentClient(path=db_path)
    return client


def _get_or_create_collection(client, settings: OrganizationKnowledgeSettings):
    """Get existing collection or create a new one."""
    collection_name = settings.chroma_collection_name
    try:
        collection = client.get_collection(collection_name)
        logger.debug("Retrieved existing collection '%s'", collection_name)
    except Exception:
        collection = client.create_collection(collection_name)
        logger.info("Created new collection '%s'", collection_name)
    return collection


def store_document_chunks(
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]],
    document_name: str,
    settings: OrganizationKnowledgeSettings | None = None,
) -> int:
    """
    Store document chunks and their embeddings in ChromaDB.

    If the collection already has data, the new chunks are added alongside existing ones.
    To replace the knowledge base, call `clear_knowledge_base()` before this.

    Args:
        chunks:         List of chunk dicts (must have "text", "chunk_id" keys).
        embeddings:     Corresponding embedding vectors (list of floats each).
        document_name:  Original filename for metadata tracking.
        settings:       Optional settings override.

    Returns:
        Number of chunks stored.
    """
    if settings is None:
        settings = get_settings()

    if not chunks or not embeddings:
        logger.warning("No chunks or embeddings to store.")
        return 0

    if len(chunks) != len(embeddings):
        raise VectorStoreError(
            f"Chunks count ({len(chunks)}) does not match embeddings count ({len(embeddings)})."
        )

    client = get_chroma_client(settings)
    collection = _get_or_create_collection(client, settings)

    ids = []
    metadatas = []
    documents = []

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_id = str(uuid4())
        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append({
            "document_name": document_name,
            "chunk_index": chunk["chunk_id"],
            "chunk_id": chunk_id,
        })

    # ChromaDB expects embeddings to be passed with the add call
    try:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
    except Exception as exc:
        if "dimension" in str(exc).lower():
            logger.warning(
                "Dimension mismatch detected (%s). Recreating collection '%s'...",
                exc,
                settings.chroma_collection_name,
            )
            try:
                client.delete_collection(settings.chroma_collection_name)
            except Exception:
                pass
            collection = client.create_collection(settings.chroma_collection_name)
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
        else:
            raise exc

    logger.info(
        "Stored %d chunks from '%s' in ChromaDB collection '%s'",
        len(chunks),
        document_name,
        settings.chroma_collection_name,
    )
    return len(chunks)



def search_similar(
    query_embedding: List[float],
    top_k: int | None = None,
    settings: OrganizationKnowledgeSettings | None = None,
) -> List[Dict[str, Any]]:
    """
    Search the vector store for chunks most similar to the query embedding.

    Args:
        query_embedding: The embedding vector of the user's question.
        top_k:           Number of results to return. Defaults to settings.top_k.
        settings:        Optional settings override.

    Returns:
        A list of dicts, each containing:
          - "text":       The chunk text.
          - "score":      Cosine distance (lower = more similar).
          - "metadata":   Dict with document_name, chunk_index, etc.
    """
    if settings is None:
        settings = get_settings()

    if top_k is None:
        top_k = settings.top_k

    client = get_chroma_client(settings)

    try:
        collection = _get_or_create_collection(client, settings)
    except Exception as exc:
        logger.warning("Could not access collection: %s", exc)
        return []

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        logger.error("ChromaDB query failed: %s", exc)
        return []

    # Parse results into a clean list of dicts
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved = []
    for doc_text, metadata, distance in zip(documents, metadatas, distances):
        retrieved.append({
            "text": doc_text,
            "score": float(distance),
            "metadata": metadata,
        })

    # Sort by score ascending (lower distance = more relevant)
    retrieved.sort(key=lambda x: x["score"])

    logger.debug(
        "Retrieved %d chunks (top_k=%d)",
        len(retrieved),
        top_k,
    )
    return retrieved


def get_collection_count(settings: OrganizationKnowledgeSettings | None = None) -> int:
    """
    Get the number of stored chunks in the collection.

    Returns 0 if the collection doesn't exist yet.
    """
    if settings is None:
        settings = get_settings()

    try:
        client = get_chroma_client(settings)
        collection = client.get_collection(settings.chroma_collection_name)
        return collection.count()
    except Exception:
        return 0


def get_stored_document_names(settings: OrganizationKnowledgeSettings | None = None) -> List[str]:
    """
    Get the list of unique document names stored in the collection.
    """
    if settings is None:
        settings = get_settings()

    try:
        client = get_chroma_client(settings)
        collection = client.get_collection(settings.chroma_collection_name)
        results = collection.get(include=["metadatas"])
        metadatas = results.get("metadatas", [])
        doc_names = set()
        for m in metadatas:
            name = m.get("document_name", "unknown")
            doc_names.add(name)
        return sorted(doc_names)
    except Exception:
        return []


def clear_knowledge_base(settings: OrganizationKnowledgeSettings | None = None) -> bool:
    """
    Delete the entire collection to replace the knowledge base.

    Args:
        settings: Optional settings override.

    Returns:
        True if cleared, False if the collection didn't exist.
    """
    if settings is None:
        settings = get_settings()

    try:
        client = get_chroma_client(settings)
        client.delete_collection(settings.chroma_collection_name)
        logger.info(
            "Deleted collection '%s' — knowledge base cleared.",
            settings.chroma_collection_name,
        )
        return True
    except Exception as exc:
        logger.warning("No collection to delete: %s", exc)
        return False

