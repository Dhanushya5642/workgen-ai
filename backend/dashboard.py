import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.meeting_summarizer import summarize_meeting
from backend.research_engine import generate_research_package
from backend.journal_ai import run_journal_ai


def run_dashboard():
    try:
        import streamlit as st
    except ImportError:
        print("Streamlit is not installed. Install it with: pip install streamlit")
        return

    st.set_page_config(page_title="AgentX", layout="wide")
    st.title("🤖 AgentX AI Productivity System")

    menu = st.sidebar.selectbox(
        "Select Module",
        [
            "Meeting Summarizer",
            "Research Copilot",
            "Journal AI"
        ]
    )


# ---------------- MEETING SUMMARIZER ---------------- #

    if menu == "Meeting Summarizer":

        st.header("Meeting Summarizer")

        transcript = st.text_area("Paste meeting transcript")

        if st.button("Generate Summary"):

            result = summarize_meeting(transcript)

            st.subheader("Summary")
            st.write(result["summary"])

            st.subheader("Decisions")
            for d in result["decisions"]:
                st.write("-", d)

            st.subheader("Action Items")
            for a in result["actions"]:
                st.write("-", a)


# ---------------- RESEARCH COPILOT ---------------- #

elif menu == "Research Copilot":

    st.header("Research Copilot")

    topic = st.text_input("Enter research topic")

    if st.button("Generate Research Package"):

        data = generate_research_package(topic)

        st.subheader("Overview")
        st.write(data["overview"])

        st.subheader("Outline")
        for o in data["outline"]:
            st.write("-", o)


# ---------------- JOURNAL ---------------- #

elif menu == "Journal AI":

    st.header("AI Journal")

    entry = st.text_area("Write your journal entry")

    if st.button("Analyze Emotion"):

        st.write("Emotion analysis will appear here.")