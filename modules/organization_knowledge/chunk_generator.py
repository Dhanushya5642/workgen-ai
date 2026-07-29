"""
Chunk Generator — splits extracted document text into meaningful, overlapping chunks.

Uses a recursive character text splitter to maintain semantic coherence:
  - Splits on paragraph boundaries first, then sentences, then character count.
  - Overlap between chunks ensures context is preserved across boundaries.
"""

from __future__ import annotations

import logging
import re
from typing import List

from modules.organization_knowledge.config import OrganizationKnowledgeSettings, get_settings

logger = logging.getLogger("org_knowledge.chunk_generator")


def generate_chunks(
    text: str,
    settings: OrganizationKnowledgeSettings | None = None,
) -> List[dict]:
    """
    Split extracted document text into chunks with metadata.

    Each chunk is returned as a dict with:
      - "text":      The chunk text content.
      - "chunk_id":  Zero-based index of the chunk.
      - "char_count": Number of characters in the chunk.

    Args:
        text:     The full extracted text from the document.
        settings: Optional settings override. If omitted, uses defaults.

    Returns:
        A list of chunk dicts.
    """
    if settings is None:
        settings = get_settings()

    chunk_size = settings.chunk_size
    chunk_overlap = settings.chunk_overlap

    # First attempt: split by double newlines (paragraphs)
    paragraphs = _split_by_paragraphs(text)

    chunks = []
    current_chunk = ""
    current_chunk_start_idx = 0

    for para in paragraphs:
        # If adding this paragraph would exceed chunk_size, save current chunk first
        if len(current_chunk) + len(para) + 1 > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Carry over overlap from the end of the previous chunk
            current_chunk = _get_overlap_tail(current_chunk, chunk_overlap)
            current_chunk_start_idx += len(current_chunk)
        current_chunk += "\n\n" + para if current_chunk else para

    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # If splitting by paragraphs produced nothing (e.g., single giant paragraph),
    # fall back to splitting by character count directly
    if not chunks:
        chunks = _split_by_char_count(text, chunk_size, chunk_overlap)

    # Build final result list with metadata
    result = []
    for idx, chunk_text in enumerate(chunks):
        result.append({
            "chunk_id": idx,
            "text": chunk_text,
            "char_count": len(chunk_text),
        })

    logger.info(
        "Generated %d chunks (chunk_size=%d, overlap=%d)",
        len(chunks),
        chunk_size,
        chunk_overlap,
    )
    return result


def _split_by_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs using double newlines / line breaks."""
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Split on two or more newlines
    paragraphs = re.split(r"\n\n+", text)
    return [p.strip() for p in paragraphs if p.strip()]


def _get_overlap_tail(text: str, overlap_chars: int) -> str:
    """Extract the last `overlap_chars` characters from text for continuity."""
    if len(text) <= overlap_chars:
        return text
    # Try to find a sentence or word boundary within the overlap window
    tail = text[-overlap_chars:]
    # Look for a newline or period to start from
    boundary = tail.find("\n")
    if boundary == -1:
        boundary = tail.find(". ")
    if boundary != -1 and boundary < len(tail) - 1:
        return tail[boundary + 1:]
    return tail


def _split_by_char_count(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Fallback: split text purely by character count with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap
    return [c for c in chunks if c]

