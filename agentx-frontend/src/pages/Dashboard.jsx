import { useEffect, useRef, useState } from "react";

const COMMANDS = [
  {
    match: /^(email|email intelligence|mail|inbox)$/i,
    path: "/email",
    reply: "On it!",
  },
  {
    match: /^(meeting|meetings|meeting intelligence|calendar|schedule)$/i,
    path: "/meeting",
    reply: "Let's go!",
  },
  {
    match:
      /^(organization|organizational knowledge|knowledge|docs|library|notes)$/i,
    path: "/organization",
    reply: "Gotcha!",
  },
  {
    match: /^(knowledge hub|hub|saved insights|entries)$/i,
    path: "/knowledge-hub",
    reply: "On it!",
  },
  {
    match: /^(research|research copilot|analytics|insights|analysis|reports)$/i,
    path: "/research",
    reply: "On it!",
  },
  {
    match: /^(journal|journal ai|mood|emotion|stress|focus)$/i,
    path: "/journal",
    reply: "Gotcha!",
  },
  {
    match: /^(pipeline|meeting pipeline|live transcript|live transcription)$/i,
    path: "/pipeline",
    reply: "Let's go!",
  },
  { match: /^(home|dashboard|main)$/i, path: "/", reply: "Back home!" },
];

const CASUAL_REPLIES = [
  { match: /\b(hi|hello|hey)\b/i, reply: "Heyyy!" },
  { match: /\b(thanks|thank you)\b/i, reply: "Anytime!" },
  { match: /\b(bye|goodbye|see you)\b/i, reply: "Catch you later!" },
];

const SpeechRecognitionCtor =
  typeof window !== "undefined"
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;

function cleanTranscript(text) {
  return text
    .toLowerCase()
    .replace(/[.,!?]/g, "")
    .trim();
}

function resolveReply(transcript) {
  const clean = cleanTranscript(transcript);

  for (const rule of CASUAL_REPLIES) {
    if (rule.match.test(clean)) {
      return { type: "casual", reply: rule.reply };
    }
  }

  for (const rule of COMMANDS) {
    if (rule.match.test(clean)) {
      return { type: "navigate", reply: rule.reply, path: rule.path };
    }
  }

  return {
    type: "unknown",
    reply:
      "Say Email Intelligence, Meeting Intelligence, Organizational Knowledge, Knowledge Hub, Research Copilot, Journal AI, Meeting Pipeline, or Home.",
  };
}

export default function Dashboard({ onNavigate, theme }) {
  const dark = theme === "dark";
  const [spokenText, setSpokenText] = useState("Hey, I’m VAZ. Where to?");
  const [isListeningUi, setIsListeningUi] = useState(false);
  const recognitionRef = useRef(null);
  const speakingRef = useRef(false);
  const listeningRef = useRef(false);
  const activeRef = useRef(true);

  const stopSession = () => {
    activeRef.current = false;
    speakingRef.current = false;
    listeningRef.current = false;
    setIsListeningUi(false);
    window.speechSynthesis?.cancel?.();
    stopListening();
  };

  const stopListening = () => {
    const recognition = recognitionRef.current;

    if (!recognition) return;

    listeningRef.current = false;

    try {
      recognition.onresult = null;
      recognition.onend = null;
      recognition.onerror = null;
      recognition.abort();
    } catch {
      // Ignore abort errors from browsers that already closed the session.
    }
  };

  const speak = (text, afterSpeak) => {
    if (typeof window === "undefined") return;

    window.speechSynthesis.cancel();
    setSpokenText(text);
    speakingRef.current = true;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.02;
    utterance.pitch = 1.06;
    utterance.onend = () => {
      speakingRef.current = false;
      if (activeRef.current) afterSpeak?.();
    };
    utterance.onerror = () => {
      speakingRef.current = false;
      if (activeRef.current) afterSpeak?.();
    };

    window.speechSynthesis.speak(utterance);
  };

  const startListening = () => {
    const recognition = recognitionRef.current;

    if (!recognition || listeningRef.current || !activeRef.current) return;

    try {
      recognition.start();
      listeningRef.current = true;
      setIsListeningUi(true);
      setSpokenText("Where to?");
    } catch {
      listeningRef.current = false;
      setIsListeningUi(false);
    }
  };

  const promptForCommand = () => {
    if (!activeRef.current) return;

    if (!SpeechRecognitionCtor) {
      setSpokenText("Voice commands need a supported browser.");
      return;
    }

    speak("Where to?", startListening);
  };

  useEffect(() => {
    activeRef.current = true;

    if (!SpeechRecognitionCtor) {
      setSpokenText("Voice commands need a supported browser.");
      return () => {
        activeRef.current = false;
      };
    }

    const recognition = new SpeechRecognitionCtor();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      listeningRef.current = false;
      setIsListeningUi(false);

      const transcript = event.results?.[0]?.[0]?.transcript || "";
      const result = resolveReply(transcript);

      if (result.type === "navigate") {
        speak(result.reply, () => {
          stopSession();
          onNavigate(result.path);
        });
        return;
      }
      if (result.type === "casual") {
        speak(
          result.reply,
          result.reply === "Catch you later!" ? undefined : promptForCommand,
        );
        return;
      }
      speak(result.reply, promptForCommand);
    };

    recognition.onend = () => {
      setIsListeningUi(false);
      if (!activeRef.current || speakingRef.current || listeningRef.current)
        return;
      promptForCommand();
    };

    recognition.onerror = () => {
      listeningRef.current = false;
      setIsListeningUi(false);
      if (!activeRef.current) return;
      promptForCommand();
    };

    recognitionRef.current = recognition;

    speak("Hey, I’m VAZ. Where to?", startListening);

    return () => {
      stopSession();
      recognitionRef.current = null;
    };
  }, [onNavigate]);

  return (
    <div className="vaz-stage flex min-h-[calc(100vh-2rem)] items-center justify-center px-2 py-6 sm:px-4">
      <section
        className={`vaz-shell w-full max-w-4xl overflow-hidden rounded-[40px] border px-6 py-10 shadow-[0_0_80px_rgba(56,189,248,0.16)] backdrop-blur-2xl sm:px-10 sm:py-14 ${
          dark
            ? "border-cyan-400/15 bg-slate-950/70"
            : "border-[#C7D7E0] bg-[#F8FBFF]/80"
        }`}
      >
        <div className="flex flex-col items-center text-center">
          <div className="vaz-orb-wrap relative flex items-center justify-center">
            <div className="vaz-orb-halo" />
            <div className="vaz-orb-core" />
            <div className="vaz-orb-ring" />
            <div className="vaz-orb-sheen" />
          </div>

          <div
            className={`mt-8 text-[0.72rem] font-semibold uppercase tracking-[0.42em] ${dark ? "text-cyan-300" : "text-sky-700"}`}
          >
            VAZ
          </div>

          <h2 className="mt-4 text-4xl font-semibold tracking-[0.32em] sm:text-5xl">
            VAZ
          </h2>

          <p
            aria-live="polite"
            className={`mt-6 max-w-2xl text-sm leading-7 sm:text-base ${dark ? "text-slate-300" : "text-slate-600"}`}
          >
            {spokenText}
          </p>

          <div
            className={`mt-4 inline-flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-[0.32em] ${
              isListeningUi
                ? dark
                  ? "border-cyan-400/30 bg-cyan-400/10 text-cyan-300"
                  : "border-sky-500/30 bg-sky-500/10 text-sky-700"
                : dark
                  ? "border-white/10 bg-white/5 text-slate-500"
                  : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-500"
            }`}
          >
            <span
              className={`h-2.5 w-2.5 rounded-full ${isListeningUi ? "bg-cyan-300 shadow-[0_0_16px_rgba(103,232,249,0.8)]" : "bg-current opacity-50"}`}
            />
            {isListeningUi ? "Listening" : "Idle"}
          </div>

          <p
            className={`mt-4 text-xs uppercase tracking-[0.32em] ${dark ? "text-slate-500" : "text-slate-400"}`}
          >
            Home · Email Intelligence · Meeting Intelligence · Organizational
            Knowledge · Knowledge Hub · Research Copilot · Meeting Pipeline
          </p>
        </div>
      </section>
    </div>
  );
}
