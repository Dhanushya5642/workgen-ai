import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.meeting_summarizer import summarize_meeting
from backend.notion_writer import write_summary


# ---------------- SAMPLE TRANSCRIPT ---------------- #

sample_transcript = """
Alice: We need to finish the AgentX meeting summarizer.
Bob: I'll integrate the Notion API.
Charlie: I'll test the system tomorrow.
Alice: Let's present it Friday.
"""


# ---------------- PIPELINE FUNCTION ---------------- #

def run_meeting_pipeline():

    print("\n===== AgentX Meeting Pipeline =====\n")

    choice = input("Use sample transcript? (y/n): ")

    if choice.lower() == "y":
        transcript = sample_transcript

    else:
        transcript = input("\nEnter meeting transcript:\n\n")

    print("\nGenerating meeting summary...\n")

    summary = summarize_meeting(transcript)

    if not summary:
        print("❌ Failed to generate summary")
        return

    print("\n===== SUMMARY =====\n")
    print(summary)

    try:
        write_summary(summary)
        print("\n✅ Summary saved to Notion")

    except Exception as e:
        print("\n⚠ Failed to save to Notion:", e)


# ---------------- STANDALONE RUN ---------------- #

if __name__ == "__main__":
    run_meeting_pipeline()