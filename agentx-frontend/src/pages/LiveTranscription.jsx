import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ResultCard from "../components/ResultCard";
import { sendAudioChunk } from "../services/api";

function normalizeSegments(data) {
  if (Array.isArray(data?.segments))
    return data.segments.map((item) => item.text || item);
  if (Array.isArray(data?.chunks))
    return data.chunks.map((item) => item.text || item);
  if (Array.isArray(data?.lines)) return data.lines;
  if (typeof data?.transcript === "string")
    return data.transcript.split(/\n+/).filter(Boolean);
  if (data?.transcript) return [data.transcript];
  return [];
}

export default function LiveTranscription({ theme }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [segments, setSegments] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [processingChunk, setProcessingChunk] = useState(false);

  const streamRef = useRef(null);
  const chunkIndexRef = useRef(0);
  const durationTimerRef = useRef(null);
  const segmentTimerRef = useRef(null);
  const currentRecorderRef = useRef(null);
  const isActiveRef = useRef(false);

  const transcript = useMemo(() => segments.join(" "), [segments]);

  /**
   * Create a new MediaRecorder, record for `durationMs` ms, then stop and return the blob.
   * This ensures each blob is a complete, standalone audio file with proper headers.
   */
  const recordSegment = useCallback((durationMs) => {
    return new Promise((resolve, reject) => {
      if (!streamRef.current || !isActiveRef.current) {
        reject(new Error("No stream"));
        return;
      }

      try {
        const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm";

        const recorder = new MediaRecorder(streamRef.current, { mimeType });
        currentRecorderRef.current = recorder;
        const chunks = [];

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) {
            chunks.push(e.data);
          }
        };

        recorder.onstop = () => {
          currentRecorderRef.current = null;
          if (chunks.length === 0) {
            reject(new Error("No audio data"));
            return;
          }
          const blob = new Blob(chunks, { type: mimeType });
          resolve(blob);
        };

        recorder.onerror = (err) => {
          currentRecorderRef.current = null;
          reject(err);
        };

        recorder.start();

        // Stop after the specified duration
        setTimeout(() => {
          if (recorder.state !== "inactive") {
            try {
              recorder.stop();
            } catch {}
          }
        }, durationMs);
      } catch (err) {
        reject(err);
      }
    });
  }, []);

  // Process a single segment: record, send, display
  const processSegment = useCallback(
    async (segmentIndex) => {
      if (!isActiveRef.current) return;

      setProcessingChunk(true);

      try {
        // Record 6 seconds of audio
        const blob = await recordSegment(6000);
        if (!isActiveRef.current) return;

        // Send to backend
        const response = await sendAudioChunk(blob, segmentIndex);
        if (!isActiveRef.current) return;

        const newSegments = normalizeSegments(response);
        if (newSegments.length > 0) {
          setSegments((prev) => [...prev, ...newSegments]);
        }
      } catch (err) {
        if (isActiveRef.current) {
          setError((prev) =>
            prev
              ? `${prev}\nSegment ${segmentIndex} failed: ${err.message}`
              : `Segment ${segmentIndex} failed: ${err.message}`,
          );
        }
      } finally {
        if (isActiveRef.current) {
          setProcessingChunk(false);
        }
      }
    },
    [recordSegment],
  );

  // Stop everything
  const stopListening = useCallback(() => {
    isActiveRef.current = false;
    setIsListening(false);
    setProcessingChunk(false);
    setLoading(false);

    if (
      currentRecorderRef.current &&
      currentRecorderRef.current.state !== "inactive"
    ) {
      try {
        currentRecorderRef.current.stop();
      } catch {}
      currentRecorderRef.current = null;
    }
    if (segmentTimerRef.current) {
      clearTimeout(segmentTimerRef.current);
      segmentTimerRef.current = null;
    }
    if (durationTimerRef.current) {
      clearInterval(durationTimerRef.current);
      durationTimerRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  // Start listening
  const startListening = useCallback(async () => {
    setError("");
    setSegments([]);
    setRecordingDuration(0);
    setProcessingChunk(false);
    setLoading(true);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!isActiveRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }

      streamRef.current = stream;
      chunkIndexRef.current = 0;
      setIsListening(true);
      setLoading(false);

      // Track recording duration
      const startTime = Date.now();
      durationTimerRef.current = setInterval(() => {
        setRecordingDuration(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);

      // Start the first segment immediately
      processSegment(chunkIndexRef.current);
      chunkIndexRef.current += 1;

      // Schedule subsequent segments every 6.5 seconds
      // (6s recording + 0.5s buffer for network)
      segmentTimerRef.current = setInterval(() => {
        if (isActiveRef.current) {
          const idx = chunkIndexRef.current;
          chunkIndexRef.current += 1;
          processSegment(idx);
        }
      }, 6500);
    } catch (err) {
      if (
        err.name === "NotAllowedError" ||
        err.name === "PermissionDeniedError"
      ) {
        setError(
          "Microphone access denied. Please allow microphone access and try again.",
        );
      } else {
        setError(err.message || "Unable to access microphone.");
      }
      setLoading(false);
      setIsListening(false);
      isActiveRef.current = false;
    }
  }, [processSegment]);

  // Toggle handler
  const handleToggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      isActiveRef.current = true;
      startListening();
    }
  }, [isListening, stopListening, startListening]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isActiveRef.current = false;
      stopListening();
    };
  }, [stopListening]);

  // Format duration as mm:ss
  const formattedDuration = useMemo(() => {
    const mins = Math.floor(recordingDuration / 60);
    const secs = recordingDuration % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
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
                : theme === 'dark'
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
        <div className={`flex flex-wrap items-center gap-3 text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-stone-500'}`}>
          <span
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 ${
              isListening
                ? theme === 'dark'
                  ? "border-rose-400/30 bg-rose-500/10 text-rose-300"
                  : "border-rose-600/20 bg-rose-600/10 text-rose-700 font-semibold"
                : theme === 'dark'
                  ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-300"
                  : "border-forest/20 bg-forest/10 text-forest font-semibold"
            }`}
          >
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                isListening 
                  ? theme === 'dark' ? "bg-rose-300 animate-pulse" : "bg-rose-600 animate-pulse"
                  : theme === 'dark' ? "bg-emerald-300" : "bg-forest"
              }`}
            />
            {isListening
              ? `Recording… ${formattedDuration}`
              : loading
                ? "Starting…"
                : 'Tap "Start Listening" to begin'}
          </span>
          {processingChunk && (
            <span className={`inline-flex items-center gap-1.5 ${theme === 'dark' ? 'text-cyan-300' : 'text-clay font-semibold'}`}>
              <svg
                className="h-3.5 w-3.5 animate-spin"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Transcribing…
            </span>
          )}
          <span>
            Records 6-second segments continuously. Each segment is sent as a
            complete audio file for transcription.
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
          <div className={`mt-3 text-xs ${theme === 'dark' ? 'text-slate-500' : 'text-stone-500'}`}>
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
            {transcript ? (
              <>
                {segments.map((segment, i) => (
                  <span key={i}>
                    {segment}
                    {i < segments.length - 1 && " "}
                  </span>
                ))}
                {processingChunk && (
                  <span className={`inline-block h-4 w-1.5 ml-0.5 animate-pulse ${theme === 'dark' ? 'bg-cyan-400' : 'bg-clay'}`} />
                )}
              </>
            ) : (
              <span className={theme === 'dark' ? 'text-slate-500' : 'text-stone-400'}>
                {isListening
                  ? "Listening… transcribed text will appear here in a moment."
                  : "The live transcript will appear here once you start recording."}
              </span>
            )}
          </div>
        </ResultCard>

        <ResultCard title="Session Info" theme={theme}>
          <div className={`space-y-3 text-sm ${theme === 'dark' ? 'text-slate-300' : 'text-stone-750'}`}>
            <div
              className={`rounded-2xl border px-4 py-3 ${
                theme === "dark"
                  ? "border-white/10 bg-white/5"
                  : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-800"
              }`}
            >
              <span className="font-semibold">Status:</span>{" "}
              <span
                className={isListening 
                  ? theme === 'dark' ? "text-rose-300" : "text-rose-700 font-semibold"
                  : theme === 'dark' ? "text-emerald-300" : "text-forest font-semibold"}
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
              <span className="font-semibold">Segment length:</span> 6 seconds
            </div>
          </div>
        </ResultCard>
      </div>
    </div>
  );
}
