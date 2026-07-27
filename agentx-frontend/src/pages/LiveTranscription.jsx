import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ResultCard from '../components/ResultCard'
import { sendAudioForTranscription } from '../services/api'

function normalizeSegments(data) {
  if (Array.isArray(data?.segments)) return data.segments.map((item) => item.text || item)
  if (Array.isArray(data?.chunks)) return data.chunks.map((item) => item.text || item)
  if (Array.isArray(data?.lines)) return data.lines
  if (typeof data?.transcript === 'string') return data.transcript.split(/\n+/).filter(Boolean)
  return []
}

export default function LiveTranscription({ theme }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [segments, setSegments] = useState([])
  const [visibleSegments, setVisibleSegments] = useState([])
  const [meta, setMeta] = useState(null)
  const [isListening, setIsListening] = useState(false)

  const mediaRecorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])

  // Animate segments appearing one by one
  useEffect(() => {
    if (!segments.length) return undefined

    setVisibleSegments([])
    let index = 0

    const timer = setInterval(() => {
      setVisibleSegments((current) => [...current, segments[index]])
      index += 1
      if (index >= segments.length) clearInterval(timer)
    }, 350)

    return () => clearInterval(timer)
  }, [segments])

  const transcript = useMemo(() => visibleSegments.join(' '), [visibleSegments])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    setIsListening(false)
  }, [])

  const startListening = useCallback(async () => {
    setError('')
    setLoading(true)

    try {
      // Request browser microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      // Set up MediaRecorder to capture in chunks
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = recorder
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      recorder.onstop = async () => {
        // Combine chunks into a single blob and send to backend
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        if (blob.size === 0) {
          setLoading(false)
          setIsListening(false)
          return
        }

        try {
          const response = await sendAudioForTranscription(blob)
          setMeta(response)
          setSegments(normalizeSegments(response))
        } catch (err) {
          setError(err.message || 'Transcription failed.')
        } finally {
          setLoading(false)
        }
      }

      // Record for 5 seconds then stop automatically
      recorder.start()
      setIsListening(true)

      setTimeout(() => {
        if (recorder.state !== 'inactive') {
          recorder.stop()
        }
      }, 5000)

    } catch (err) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Microphone access denied. Please allow microphone access and try again.')
      } else {
        setError(err.message || 'Unable to access microphone.')
      }
      setLoading(false)
      setIsListening(false)
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording()
    }
  }, [stopRecording])

  return (
    <div className="space-y-6">
      <ResultCard
        title="Live Transcription"
        subtitle="Record audio from your browser microphone and get real-time speech-to-text transcription."
        theme={theme}
        actions={
          <button
            type="button"
            onClick={isListening ? stopRecording : startListening}
            disabled={loading && !isListening}
            className={`rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
              isListening
                ? 'bg-rose-500 text-white hover:bg-rose-400'
                : 'bg-cyan-400 text-slate-950 hover:bg-cyan-300'
            }`}
          >
            {loading ? 'Processing…' : isListening ? 'Stop' : 'Start Listening'}
          </button>
        }
      >
        <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400">
          <span
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 ${
              isListening
                ? 'border-rose-400/30 bg-rose-500/10 text-rose-300'
                : 'border-emerald-400/30 bg-emerald-500/10 text-emerald-300'
            }`}
          >
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                isListening ? 'bg-rose-300 animate-pulse' : 'bg-emerald-300'
              }`}
            />
            {isListening
              ? 'Recording… (5s)'
              : loading
                ? 'Transcribing…'
                : 'Tap "Start Listening" to begin'}
          </span>
          <span>Records 5 seconds of audio from your browser microphone</span>
        </div>
        {error ? (
          <div className="mt-4 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
            {error}
          </div>
        ) : null}
      </ResultCard>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <ResultCard title="Real-time Transcript" subtitle="Streaming display" theme={theme}>
          <div
            className={`min-h-[320px] rounded-[28px] border p-5 text-sm leading-8 ${
              theme === 'dark'
                ? 'border-white/10 bg-slate-950/70 text-slate-200'
                : 'border-slate-200 bg-slate-50 text-slate-700'
            }`}
          >
            {transcript || 'The live transcript will appear here once the backend returns speech-to-text output.'}
          </div>
        </ResultCard>

        <ResultCard title="Session Metadata" theme={theme}>
          <div className="space-y-3 text-sm text-slate-300">
            {meta ? (
              Object.entries(meta)
                .filter(([key]) => !['segments', 'chunks', 'lines', 'transcript'].includes(key))
                .map(([key, value]) => (
                  <div
                    key={key}
                    className={`rounded-2xl border px-4 py-3 ${
                      theme === 'dark'
                        ? 'border-white/10 bg-white/5'
                        : 'border-slate-200 bg-slate-50 text-slate-700'
                    }`}
                  >
                    <span className="font-semibold capitalize">{key.replace(/_/g, ' ')}:</span>{' '}
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </div>
                ))
            ) : (
              <div className="rounded-2xl border border-dashed border-white/10 px-4 py-5 text-sm text-slate-400">
                No session metadata yet.
              </div>
            )}
          </div>
        </ResultCard>
      </div>
    </div>
  )
}

