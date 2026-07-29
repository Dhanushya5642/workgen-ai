import ollama
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.meeting_summarizer import summarize_meeting

text = input("Enter meeting transcript:\n")

result = summarize_meeting(text)

print("\nMeeting Summary")
print(result["summary"])

print("\nDecisions")
for d in result["decisions"]:
    print("-", d)

print("\nAction Items")
for a in result["actions"]:
    print("-", a)

print("\nNext Steps")
for s in result["next_steps"]:
    print("-", s)