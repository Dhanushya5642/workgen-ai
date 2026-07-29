import streamlit as st
import threading

# import your backend functions
from main import (
    automation_loop,
    run_meeting_summarizer,
    run_research_engine,
    run_journal_ai,
    run_meeting_pipeline,
    run_live_transcription,
    run_dashboard
)

st.set_page_config(page_title="AgentX", layout="wide")

st.title("🤖 AgentX - AI Productivity OS")

st.sidebar.title("Modules")

choice = st.sidebar.selectbox(
    "Choose Module",
    [
        "Email Automation",
        "Meeting Summarizer",
        "Research Copilot",
        "Journal AI",
        "Meeting Pipeline",
        "Live Transcription",
        "Dashboard"
    ]
)

# ---------------- EMAIL ---------------- #

if choice == "Email Automation":

    st.header("📩 Email → Calendar + Notion Automation")

    if st.button("Start Automation"):

        st.success("Running in background...")

        thread = threading.Thread(target=automation_loop)
        thread.start()

# ---------------- MEETING ---------------- #

elif choice == "Meeting Summarizer":

    st.header("📝 Meeting Summarizer")

    transcript = st.text_area("Paste meeting transcript")

    if st.button("Summarize"):

        if transcript:
            result = run_meeting_summarizer(transcript)

            st.subheader("Summary")
            st.write(result.get("summary", ""))

            st.subheader("Actions")
            st.write(result.get("actions", []))
        else:
            st.warning("Enter transcript")

# ---------------- RESEARCH ---------------- #

elif choice == "Research Copilot":

    st.header("🔍 Research AI")

    if st.button("Run"):
        if run_research_engine:
            run_research_engine()
        else:
            st.error("Module not available")

# ---------------- JOURNAL ---------------- #

elif choice == "Journal AI":

    st.header("📔 Journal AI")

    if st.button("Open"):
        if run_journal_ai:
            run_journal_ai()
        else:
            st.error("Module not available")

# ---------------- PIPELINE ---------------- #

elif choice == "Meeting Pipeline":

    st.header("⚙ Meeting Pipeline")

    if st.button("Run"):
        if run_meeting_pipeline:
            run_meeting_pipeline()
        else:
            st.error("Module not available")

# ---------------- LIVE ---------------- #

elif choice == "Live Transcription":

    st.header("🎙 Live Transcription")

    if st.button("Start"):
        if run_live_transcription:
            run_live_transcription()
        else:
            st.error("Module not available")

# ---------------- DASHBOARD ---------------- #

elif choice == "Dashboard":

    st.header("📊 Dashboard")

    if st.button("Open"):
        if run_dashboard:
            run_dashboard()
        else:
            st.error("Module not available")