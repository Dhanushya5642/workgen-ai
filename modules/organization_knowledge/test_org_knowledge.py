"""
Integration test for Organization Knowledge Module.

Tests document ingestion, vector storage, semantic retrieval, and QA engine with hallucination prevention.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from modules.organization_knowledge.orchestrator import OrganizationKnowledgeOrchestrator

logging.basicConfig(level=logging.INFO)


def run_test():
    print("=== Testing Organization Knowledge Module ===")
    orchestrator = OrganizationKnowledgeOrchestrator()

    sample_doc_content = """
    SRI ESHWAR COLLEGE RULES AND REGULATIONS

    1. DRESS CODE POLICY
    Formal dress is mandatory on Mondays for all students.
    Jeans, T-shirts, and casual sneakers are strictly not permitted on Mondays.
    Smart casual attire is allowed from Tuesday to Friday.

    2. TIMINGS & ATTENDANCE
    College hours are from 8:45 AM to 4:30 PM.
    Minimum required attendance to appear for exams is 75%.
    Late arrival beyond 9:00 AM will be marked as half-day leave.

    3. HOSTEL REGULATIONS
    Hostel gates close strictly at 7:00 PM for all residents.
    Quiet hours must be observed between 10:00 PM and 6:00 AM.
    """

    filename = "Sri Eshwar College Rules.txt"
    file_bytes = sample_doc_content.encode("utf-8")

    print(f"\n1. Ingesting sample document '{filename}'...")
    upload_result = orchestrator.upload_document(file_bytes=file_bytes, filename=filename)
    print(f"Upload Result: {upload_result}")

    assert upload_result["success"] is True, "Upload failed!"
    assert upload_result["chunks_count"] > 0, "No chunks stored!"

    print("\n2. Checking Knowledge Base Status...")
    status = orchestrator.get_status()
    print(f"Status: {status}")
    assert status["has_documents"] is True, "Status indicates no documents!"
    assert status["total_chunks"] > 0, "Total chunks count is 0!"

    print("\n3. Testing Question 1 (Information present in document):")
    q1 = "Can I wear jeans on Monday?"
    ans1 = orchestrator.ask_question(q1)
    print(f"Question: {q1}")
    print(f"Response: {ans1['answer']}")
    print(f"Found: {ans1['found']}")

    print("\n4. Testing Question 2 (Information NOT present in document):")
    q2 = "Is beard allowed?"
    ans2 = orchestrator.ask_question(q2)
    print(f"Question: {q2}")
    print(f"Response: {ans2['answer']}")
    print(f"Found: {ans2['found']}")

    assert ans2["found"] is False, "Should be marked as not found!"
    assert "couldn't find any information" in ans2["answer"].lower() or "unavailable" in ans2["answer"].lower(), (
        f"Expected hallucination prevention message, got: {ans2['answer']}"
    )

    print("\n5. Testing Clear Knowledge Base...")
    clear_res = orchestrator.clear_knowledge_base()
    print(f"Clear Result: {clear_res}")
    status_after = orchestrator.get_status()
    assert status_after["has_documents"] is False, "Knowledge base was not cleared!"

    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    run_test()
