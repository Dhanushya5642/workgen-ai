import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.research_engine import generate_research_package


def print_research(data):
    print("\n" + "="*60)
    print("📖 OVERVIEW")
    print("="*60)
    print(data.get("overview", ""))

    print("\n🧱 OUTLINE")
    print("-"*60)
    for item in data.get("outline", []):
        print("•", item)

    print("\n📚 KEY CONCEPTS")
    print("-"*60)
    for concept in data.get("key_concepts", []):
        print("•", concept)

    print("\n❓ RESEARCH QUESTIONS")
    print("-"*60)
    for q in data.get("research_questions", []):
        print("•", q)

    print("\n📑 CITATIONS")
    print("-"*60)
    for c in data.get("citations", []):
        print("•", c)

    print("\n" + "="*60)


if __name__ == "__main__":

    topic = input("Enter research topic: ")

    result = generate_research_package(topic)

    if result:
        print_research(result)

        # ✅ Save to file properly
        with open("research.json", "w") as f:
            json.dump(result, f, indent=2)

        print("\n💾 Saved to research.json")

    else:
        print("❌ Failed to parse AI response.")