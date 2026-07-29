import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ResultCard from "../components/ResultCard";

const SpeechRecognitionCtor =
  typeof window !== "undefined"
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;

export default function LiveTranscription({ theme }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [segments, setSegments] = useState([]);
  const [liveText, setLiveText] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);

  const recognitionRef = useRef(null);
  const durationTimerRef = useRef(null);
  const isActiveRef = useRef(false);

  const transcript = useMemo(() => segments.join(" "), [segments]);
  const displayTranscript = liveText
    ? `${transcript}${transcript ? " " : ""}${liveText}`
    : transcript;

  const clearDurationTimer = useCallback(() => {
    if (durationTimerRef.current) {
      clearInterval(durationTimerRef.current);
      durationTimerRef.current = null;
    }
  }, []);

  const stopRecognition = useCallback(() => {
    const recognition = recognitionRef.current;

    if (!recognition) return;

    try {
      recognition.onresult = null;
      recognition.onend = null;
      recognition.onerror = null;
      recognition.stop();
    } catch {
      try {
        recognition.abort();
      } catch {}
    }

    recognitionRef.current = null;
  }, []);

  const stopListening = useCallback(() => {
    isActiveRef.current = false;
    setIsListening(false);
    setLoading(false);
    setLiveText("");
    clearDurationTimer();
    stopRecognition();
  }, [clearDurationTimer, stopRecognition]);

  const startListening = useCallback(async () => {
    setError("");
    setSegments([]);
    setLiveText("");
    setRecordingDuration(0);
    setLoading(true);
    isActiveRef.current = true;

    if (!SpeechRecognitionCtor) {
      setError("Speech recognition is not supported in this browser.");
      setLoading(false);
      setIsListening(false);
      isActiveRef.current = false;
      return;
    }

    try {
      const recognition = new SpeechRecognitionCtor();
      recognition.lang = "en-US";
      recognition.interimResults = true;
      recognition.continuous = true;
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        if (!isActiveRef.current) return;

        setLoading(false);
        setIsListening(true);

        const finalTexts = [];
        let interimText = "";

        for (
          let index = event.resultIndex;
          index < event.results.length;
          index += 1
        ) {
          const result = event.results[index];
          const text = result[0]?.transcript?.trim() || "";

          if (!text) continue;

          if (result.isFinal) {
            finalTexts.push(text);
          } else {
            interimText += `${text} `;
          }
        }

        if (finalTexts.length > 0) {
          setSegments((prev) => [...prev, ...finalTexts]);
          setLiveText("");
        } else {
          setLiveText(interimText.trim());
        }
      };

      recognition.onerror = (event) => {
        if (!isActiveRef.current) return;
        setError(
          event.error
            ? `Speech recognition error: ${event.error}`
            : "Speech recognition failed.",
        );
        setLoading(false);
        setIsListening(false);
        setLiveText("");
      };

      recognition.onend = () => {
        if (!isActiveRef.current) return;

        recognitionRef.current = null;

        if (!isActiveRef.current) return;

        try {
          recognition.start();
          recognitionRef.current = recognition;
        } catch {
          // If auto-restart fails, keep the current transcript visible.
        }
      };

      recognitionRef.current = recognition;
      setIsListening(true);
      setLoading(false);

      const startTime = Date.now();
      durationTimerRef.current = setInterval(() => {
        setRecordingDuration(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);

      recognition.start();
    } catch (err) {
      setError(err.message || "Unable to start speech recognition.");
      setLoading(false);
      setIsListening(false);
      setLiveText("");
      isActiveRef.current = false;
      clearDurationTimer();
      stopRecognition();
    }
  }, [clearDurationTimer, stopRecognition]);

  const handleToggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      isActiveRef.current = true;
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  useEffect(() => {
    return () => {
      isActiveRef.current = false;
      stopListening();
    };
  }, [stopListening]);

  const formattedDuration = useMemo(() => {
    const mins = Math.floor(recordingDuration / 60);
    const secs = recordingDuration % 60;
    return `${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  }, [recordingDuration]);

  return (
    <div className="space-y-6">
      <ResultCard
        title="Live Transcription"
        subtitle="Continuously record audio from your browser microphone and see transcribed text appear in real-time."
        theme={theme}
        actions={
          <button
            type="button"
            onClick={handleToggleListening}
            disabled={loading && !isListening}
            className={`rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
              isListening
                ? "bg-rose-600 text-white hover:bg-rose-500"
                : theme === "dark"
                  ? "bg-cyan-400 text-slate-950 hover:bg-cyan-300"
                  : "bg-clay text-white hover:bg-clay/90"
            }`}
          >
            {loading
              ? "Starting…"
              : isListening
                ? "Stop Recording"
                : "Start Listening"}
          </button>
        }
      >
        <div
          className={`flex flex-wrap items-center gap-3 text-sm ${theme === "dark" ? "text-slate-400" : "text-stone-500"}`}
        >
          <span
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 ${
              isListening
                ? theme === "dark"
                  ? "border-rose-400/30 bg-rose-500/10 text-rose-300"
                  : "border-rose-600/20 bg-rose-600/10 text-rose-700 font-semibold"
                : theme === "dark"
                  ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-300"
                  : "border-forest/20 bg-forest/10 text-forest font-semibold"
            }`}
          >
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                isListening
                  ? theme === "dark"
                    ? "bg-rose-300 animate-pulse"
                    : "bg-rose-600 animate-pulse"
                  : theme === "dark"
                    ? "bg-emerald-300"
                    : "bg-forest"
              }`}
            />
            {isListening
              ? `Recording… ${formattedDuration}`
              : loading
                ? "Starting…"
                : 'Tap "Start Listening" to begin'}
          </span>
          <span>
            Speech is transcribed live as you talk, so text appears in the
            canvas immediately.
          </span>
        </div>
        {error ? (
          <div className="mt-4 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300 max-h-32 overflow-y-auto">
            {error.split("\n").map((line, i) => (
              <div key={i}>{line}</div>
            ))}
          </div>
        ) : null}
        {segments.length > 0 && (
          <div
            className={`mt-3 text-xs ${theme === "dark" ? "text-slate-500" : "text-stone-500"}`}
          >
            {segments.length} segment{segments.length !== 1 ? "s" : ""}{" "}
            transcribed
          </div>
        )}
      </ResultCard>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <ResultCard
          title="Real-time Transcript"
          subtitle="Streaming display — grows as each segment is transcribed"
          theme={theme}
        >
          <div
            className={`min-h-[320px] max-h-[500px] overflow-y-auto rounded-[28px] border p-5 text-sm leading-8 transition ${
              theme === "dark"
                ? "border-white/10 bg-slate-950/70 text-slate-200"
                : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-800"
            }`}
          >
            {displayTranscript ? (
              <>
                {segments.map((segment, i) => (
                  <span key={i}>
                    {segment}
                    {i < segments.length - 1 && " "}
                  </span>
                ))}
                {liveText ? (
                  <span
                    className={
                      theme === "dark" ? "text-slate-400" : "text-stone-500"
                    }
                  >
                    {segments.length > 0 ? " " : ""}
                    {liveText}
                  </span>
                ) : null}
                {isListening && (
                  <span
                    className={`inline-block h-4 w-1.5 ml-0.5 animate-pulse ${theme === "dark" ? "bg-cyan-400" : "bg-clay"}`}
                  />
                )}
              </>
            ) : (
              <span
                className={
                  theme === "dark" ? "text-slate-500" : "text-stone-400"
                }
              >
                {isListening
                  ? "Listening… transcribed text will appear here in a moment."
                  : "The live transcript will appear here once you start recording."}
              </span>
            )}
          </div>
        </ResultCard>

        <ResultCard title="Session Info" theme={theme}>
          <div
            className={`space-y-3 text-sm ${theme === "dark" ? "text-slate-300" : "text-stone-750"}`}
          >
            <div
              className={`rounded-2xl border px-4 py-3 ${
                theme === "dark"
                  ? "border-white/10 bg-white/5"
                  : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-800"
              }`}
            >
              <span className="font-semibold">Status:</span>{" "}
              <span
                className={
                  isListening
                    ? theme === "dark"
                      ? "text-rose-300"
                      : "text-rose-700 font-semibold"
                    : theme === "dark"
                      ? "text-emerald-300"
                      : "text-forest font-semibold"
                }
              >
                {isListening ? "Recording" : "Idle"}
              </span>
            </div>
            <div
              className={`rounded-2xl border px-4 py-3 ${
                theme === "dark"
                  ? "border-white/10 bg-white/5"
                  : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-800"
              }`}
            >
              <span className="font-semibold">Duration:</span>{" "}
              {isListening ? formattedDuration : "—"}
            </div>
            <div
              className={`rounded-2xl border px-4 py-3 ${
                theme === "dark"
                  ? "border-white/10 bg-white/5"
                  : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-800"
              }`}
            >
              <span className="font-semibold">Segments:</span> {segments.length}
            </div>
            <div
              className={`rounded-2xl border px-4 py-3 ${
                theme === "dark"
                  ? "border-white/10 bg-white/5"
                  : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-800"
              }`}
            >
              <span className="font-semibold">Mode:</span> Browser speech
              recognition
            </div>
          </div>
        </ResultCard>
      </div>
    </div>
  );
}
