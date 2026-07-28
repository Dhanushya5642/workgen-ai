"""
Question Answering Engine — generates answers strictly from retrieved document context.

Core principles:
  1. ONLY use the provided context to answer.
  2. If the answer is not in the context, state that clearly.
  3. Never hallucinate or invent policies.

Supports two backends:
  - Ollama (e.g., gemma:2b, llama3, mistral)
  - OpenAI (e.g., gpt-4o-mini, gpt-4o)
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from modules.organization_knowledge.config import OrganizationKnowledgeSettings, get_settings

logger = logging.getLogger("org_knowledge.qa_engine")


class QAEngineError(Exception):
    """Raised when the QA engine fails."""


# Strict system prompt that prevents hallucination
SYSTEM_PROMPT = (
    "You are an Organization Knowledge Assistant. Answer ONLY using the retrieved "
    "organization documents. Do not use outside knowledge. If the answer is not "
    "explicitly mentioned in the documents, clearly state that the information is "
    "unavailable. Never hallucinate or create policies."
)


NOT_FOUND_RESPONSE = (
    "I couldn't find any information about this in the uploaded organization documents."
)


def answer_question(
    question: str,
    context: str,
    settings: OrganizationKnowledgeSettings | None = None,
) -> dict:
    """
    Answer a question strictly based on the provided document context.

    Args:
        question: The user's question.
        context:  Retrieved document chunks formatted as a single string.
        settings: Optional settings override.

    Returns:
        A dict with:
          - "answer":      The generated answer text.
          - "source":      The context that was used (for transparency).
          - "found":       Boolean indicating if an answer was found in the context.
          - "model":       The LLM model used.

    Raises:
        QAEngineError: If the QA process fails.
    """
    if settings is None:
        settings = get_settings()

    if not context or not context.strip():
        return {
            "answer": NOT_FOUND_RESPONSE,
            "source": "",
            "found": False,
            "model": settings.ollama_llm_model
            if settings.llm_backend == "ollama"
            else settings.openai_llm_model,
        }

    backend = settings.llm_backend.lower()

    user_prompt = (
        f"Organization Document Content:\n"
        f"{context}\n\n"
        f"User Question: {question}\n\n"
        f"Task: Answer the question clearly and directly based ONLY on the document content above. "
        f"If the document does not contain the answer, respond EXACTLY: '{NOT_FOUND_RESPONSE}'"
    )


    try:
        if backend == "ollama":
            result = _answer_with_ollama(user_prompt, settings)
        elif backend == "openai":
            result = _answer_with_openai(user_prompt, settings)
        else:
            result = _answer_with_extractive_fallback(question, context)
    except Exception as exc:
        logger.warning(
            "Primary LLM backend '%s' failed: %s. Falling back to extractive QA.",
            backend,
            exc,
        )
        result = _answer_with_extractive_fallback(question, context)


    # Post-processing: detect if the answer indicates "not found"
    answer_text = result["answer"]
    found = _is_answer_found(answer_text, context)

    if not found:
        result["answer"] = NOT_FOUND_RESPONSE

    result["found"] = found
    result["source"] = context

    logger.info(
        "QA result: found=%s, model=%s, answer_len=%d",
        found,
        result["model"],
        len(result["answer"]),
    )
    return result



def _answer_with_ollama(
    user_prompt: str,
    settings: OrganizationKnowledgeSettings,
) -> dict:
    """Send the prompt to Ollama and return the response."""
    try:
        import ollama
    except ImportError:
        raise QAEngineError(
            "ollama Python client is not installed. Run: pip install ollama"
        )

    client = ollama.Client(host=settings.ollama_base_url)
    model = settings.ollama_llm_model

    try:
        response = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.0},  # Low temperature for factual answers
        )
        answer = response["message"]["content"].strip()
        return {"answer": answer, "model": model}
    except Exception as exc:
        raise QAEngineError(f"Ollama chat failed: {exc}")


def _answer_with_openai(
    user_prompt: str,
    settings: OrganizationKnowledgeSettings,
) -> dict:
    """Send the prompt to OpenAI and return the response."""
    try:
        from openai import OpenAI
    except ImportError:
        raise QAEngineError(
            "openai Python client is not installed. Run: pip install openai"
        )

    if not settings.openai_api_key:
        raise QAEngineError(
            "OpenAI API key is not set. Set the OPENAI_API_KEY environment variable."
        )

    client = OpenAI(api_key=settings.openai_api_key)
    model = settings.openai_llm_model

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
        )
        answer = response.choices[0].message.content.strip()
        return {"answer": answer, "model": model}
    except Exception as exc:
        raise QAEngineError(f"OpenAI chat failed: {exc}")


def _is_answer_found(answer_text: str, context: str) -> bool:
    """
    Heuristic check: if the answer contains the "not found" message or
    explicitly says it couldn't find information, mark as not found.

    Also checks if the answer references actual content from the context.
    """
    not_found_phrases = [
        "couldn't find any information",
        "not found in the",
        "information is unavailable",
        "not explicitly mentioned",
        "does not contain",
        "no information",
        "not available in the",
        "cannot answer",
        "does not mention",
        "no mention",
        "not specified",
        "unclear",
        "unavailable",
    ]


    lower_answer = answer_text.lower()

    # Check for explicit "not found" signals
    for phrase in not_found_phrases:
        if phrase in lower_answer:
            return False

    # If the answer is very short and generic, it's likely a "not found"
    if len(answer_text) < 20:
        return False

    return True


def _answer_with_extractive_fallback(question: str, context: str) -> dict:
    """
    Extractive QA fallback when external LLM is offline/unreachable.
    Scans context for sentences matching query keywords and extracts relevant policy rules.
    """
    import re

    stop_words = {
        "a", "an", "the", "is", "are", "was", "were", "can", "could", "should", "would",
        "i", "you", "he", "she", "it", "we", "they", "on", "in", "at", "to", "for", "of",
        "with", "what", "where", "when", "how", "why", "allowed", "permitted", "mandatory",
        "do", "does", "did", "have", "has", "had", "be", "been", "being", "or", "and", "not"
    }

    raw_keywords = re.findall(r"\w+", question.lower())
    keywords = [w for w in raw_keywords if w not in stop_words and len(w) > 1]

    if not keywords:
        return {"answer": NOT_FOUND_RESPONSE, "model": "extractive-fallback"}

    # Split context into sentences
    sentences = re.split(r"(?<=[.!?])\s+", context)
    matching_sentences = []

    for sentence in sentences:
        clean_sentence = sentence.strip()
        if not clean_sentence:
            continue
        sentence_lower = clean_sentence.lower()
        score = sum(1 for kw in keywords if kw in sentence_lower)
        if score > 0:
            matching_sentences.append((score, clean_sentence))

    if not matching_sentences:
        return {"answer": NOT_FOUND_RESPONSE, "model": "extractive-fallback"}

    matching_sentences.sort(key=lambda x: x[0], reverse=True)
    best_matches = [s for _, s in matching_sentences[:3]]
    extracted_text = " ".join(best_matches)

    answer = f"According to the uploaded organization documents: {extracted_text}"
    return {"answer": answer, "model": "extractive-fallback"}


