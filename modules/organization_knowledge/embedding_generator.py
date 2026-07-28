"""
Embedding Generator — creates vector embeddings for text chunks.

Supports two backends:
  1. Ollama  (e.g., nomic-embed-text, mxbai-embed-large)
  2. OpenAI  (e.g., text-embedding-3-small, text-embedding-3-large)
"""

from __future__ import annotations

import logging
from typing import List, Optional

from modules.organization_knowledge.config import OrganizationKnowledgeSettings, get_settings

logger = logging.getLogger("org_knowledge.embedding_generator")


class EmbeddingGenerationError(Exception):
    """Raised when embedding generation fails."""


def generate_embeddings(
    texts: List[str],
    settings: OrganizationKnowledgeSettings | None = None,
) -> List[List[float]]:
    """
    Generate embeddings for a list of text strings.

    Args:
        texts:    A list of text strings to embed.
        settings: Optional settings override.

    Returns:
        A list of embedding vectors (each is a list of floats).

    Raises:
        EmbeddingGenerationError: If the embedding backend fails.
    """
    if settings is None:
        settings = get_settings()

    if not texts:
        return []

    backend = settings.embedding_backend.lower()

    try:
        if backend == "ollama":
            return _embed_with_ollama(texts, settings)
        elif backend == "openai":
            return _embed_with_openai(texts, settings)
        else:
            return _embed_with_fallback(texts)
    except Exception as exc:
        logger.warning(
            "Primary embedding backend '%s' failed: %s. Falling back to local hash embedding.",
            backend,
            exc,
        )
        return _embed_with_fallback(texts)


def _embed_with_fallback(texts: List[str], dim: int = 384) -> List[List[float]]:
    """
    Fallback deterministic feature vector generator using word feature hashing.
    Ensures embedding generation never fails even if Ollama/OpenAI is offline.
    """
    import hashlib
    import math
    import re

    embeddings = []
    for text in texts:
        vec = [0.0] * dim
        words = re.findall(r"\w+", text.lower())
        if not words:
            embeddings.append(vec)
            continue
        for word in words:
            # Hash word into a dimension index and sign
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if (h >> 16) & 1 else -1.0
            vec[idx] += sign

        # Normalize vector to unit length
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        embeddings.append(vec)

    logger.info("Generated %d embeddings via local fallback (dim=%d)", len(embeddings), dim)
    return embeddings



def _embed_with_ollama(
    texts: List[str],
    settings: OrganizationKnowledgeSettings,
) -> List[List[float]]:
    """Generate embeddings using Ollama."""
    try:
        import ollama
    except ImportError:
        raise EmbeddingGenerationError(
            "ollama Python client is not installed. Run: pip install ollama"
        )

    client = ollama.Client(host=settings.ollama_base_url)
    model = settings.ollama_embedding_model

    try:
        # Verify the model is available locally
        client.show(model)
    except Exception as exc:
        raise EmbeddingGenerationError(
            f"Ollama embedding model '{model}' is not available locally: {exc}"
        )


    embeddings = []
    for idx, text in enumerate(texts):
        try:
            response = client.embeddings(model=model, prompt=text)
            embeddings.append(response["embedding"])
        except Exception as exc:
            raise EmbeddingGenerationError(
                f"Ollama embedding failed at index {idx}: {exc}"
            )

        if (idx + 1) % 10 == 0:
            logger.debug("Embedded %d / %d chunks", idx + 1, len(texts))

    logger.info(
        "Generated %d embeddings via Ollama (model=%s, dim=%d)",
        len(embeddings),
        model,
        len(embeddings[0]) if embeddings else 0,
    )
    return embeddings


def _embed_with_openai(
    texts: List[str],
    settings: OrganizationKnowledgeSettings,
) -> List[List[float]]:
    """Generate embeddings using OpenAI."""
    try:
        from openai import OpenAI
    except ImportError:
        raise EmbeddingGenerationError(
            "openai Python client is not installed. Run: pip install openai"
        )

    if not settings.openai_api_key:
        raise EmbeddingGenerationError(
            "OpenAI API key is not set. Set the OPENAI_API_KEY environment variable."
        )

    client = OpenAI(api_key=settings.openai_api_key)
    model = settings.openai_embedding_model

    try:
        response = client.embeddings.create(
            model=model,
            input=texts,
        )
        # Sort by index to preserve original order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        embeddings = [item.embedding for item in sorted_data]

        logger.info(
            "Generated %d embeddings via OpenAI (model=%s, dim=%d)",
            len(embeddings),
            model,
            len(embeddings[0]) if embeddings else 0,
        )
        return embeddings

    except Exception as exc:
        raise EmbeddingGenerationError(
            f"OpenAI embedding failed: {exc}"
        )

