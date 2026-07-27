import ollama
import json
import re

def summarize_meeting(transcript):

    prompt = f"""
You are a meeting assistant.

Return ONLY valid JSON:

{{
  "title": "short meeting title",
  "summary": "short summary",
  "decisions": [],
  "actions": [],
  "next_steps": []
}}

Meeting Transcript:
{transcript}
"""

    response = ollama.chat(
        model="gemma:2b",
        messages=[{"role": "user", "content": prompt}]
    )

    output = response["message"]["content"]

    output = output.replace("```json","").replace("```","")

    match = re.search(r"\{[\s\S]*\}", output)

    if match:
        return json.loads(match.group())

    return {
        "summary": "Failed to summarize",
        "decisions": [],
        "actions": [],
        "next_steps": []
    }