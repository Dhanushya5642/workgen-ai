try:
    import ollama
except ImportError:
    ollama = None

import json
import re


def extract_json(text):

    try:
        return json.loads(text)

    except:

        match = re.search(r"\{.*\}", text, re.DOTALL)

        if match:

            try:
                return json.loads(match.group())
            except:
                return None

    return None


def generate_research_package(topic):

    prompt = f"""
You are an academic research assistant.

Generate research package for topic: "{topic}"

Return STRICT JSON:

{{
  "overview": "",
  "outline": [],
  "key_concepts": [],
  "research_questions": [],
  "citations": []
}}

Only JSON. No extra text.
"""

    response = ollama.chat(
        model="gemma:2b",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.3}
    )

    raw = response["message"]["content"]

    print("\nRAW RESPONSE:\n", raw)

    return extract_json(raw)


# -------- RUN FUNCTION (USED BY MAIN MENU) -------- #

def run_research_engine():

    topic = input("\nEnter research topic: ")

    result = generate_research_package(topic)

    if not result:
        print("❌ Failed to generate research")
        return

    print("\n===== RESEARCH OVERVIEW =====")
    print(result.get("overview", ""))

    print("\n===== OUTLINE =====")
    for item in result.get("outline", []):
        print("-", item)

    print("\n===== KEY CONCEPTS =====")
    for concept in result.get("key_concepts", []):
        print("-", concept)

    print("\n===== RESEARCH QUESTIONS =====")
    for q in result.get("research_questions", []):
        print("-", q)

    print("\n===== CITATIONS =====")
    for c in result.get("citations", []):
        print("-", c)