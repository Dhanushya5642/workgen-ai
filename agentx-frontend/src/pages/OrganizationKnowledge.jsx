import { useState, useEffect, useRef } from 'react'
import ResultCard from '../components/ResultCard'
import {
  uploadOrganizationDocument,
  askOrganizationQuestion,
  getOrganizationKnowledgeStatus,
  clearOrganizationKnowledge,
} from '../services/api'

export default function OrganizationKnowledge({ theme }) {
  const [uploading, setUploading] = useState(false)
  const [asking, setAsking] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [error, setError] = useState('')
  const [status, setStatus] = useState(null)
  const [uploadResult, setUploadResult] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    fetchStatus()
  }, [])

  const fetchStatus = async () => {
    try {
      const data = await getOrganizationKnowledgeStatus()
      setStatus(data)
    } catch (err) {
      console.warn('Status fetch failed:', err)
    }
  }

  const handleFileSelect = (event) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setUploadResult(null)
      setError('')
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first.')
      return
    }
    setUploading(true)
    setError('')
    setUploadResult(null)
    try {
      const result = await uploadOrganizationDocument(selectedFile)
      setUploadResult(result)
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      fetchStatus()
    } catch (err) {
      setError(err.message || 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  const handleAsk = async () => {
    if (!question.trim()) {
      setError('Please enter a question.')
      return
    }
    setAsking(true)
    setError('')
    setAnswer(null)
    try {
      const result = await askOrganizationQuestion(question)
      setAnswer(result)
    } catch (err) {
      setError(err.message || 'Failed to get answer.')
    } finally {
      setAsking(false)
    }
  }

  const handleClear = async () => {
    if (!window.confirm('Are you sure? This will delete all uploaded documents.')) {
      return
    }
    setClearing(true)
    setError('')
    try {
      await clearOrganizationKnowledge()
      setStatus(null)
      setAnswer(null)
      setUploadResult(null)
      fetchStatus()
    } catch (err) {
      setError(err.message || 'Failed to clear knowledge base.')
    } finally {
      setClearing(false)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const dark = theme === 'dark'

  return (
    <div className="space-y-6">
      <ResultCard title="Upload Organization Document" subtitle="Upload PDF, DOCX, or TXT files. A new upload replaces the previous knowledge base." theme={theme}>
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileSelect}
              className={`block w-full max-w-md rounded-2xl border text-sm file:mr-4 file:rounded-xl file:border-0 file:px-4 file:py-2 file:text-sm file:font-semibold ${dark ? 'border-white/10 bg-slate-950/70 text-slate-50 file:bg-cyan-400 file:text-slate-950 file:hover:bg-cyan-300' : 'border-[#D3CBB8] bg-[#FAF8F5] text-stone-850 file:bg-clay file:text-white file:hover:bg-clay/90'}`}
            />
            <button type="button" onClick={handleUpload} disabled={!selectedFile || uploading} className={`rounded-2xl px-5 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${dark ? 'bg-cyan-400 text-slate-950 hover:bg-cyan-300' : 'bg-clay text-white hover:bg-clay/90'}`}>
              {uploading ? 'Uploading & Processing...' : 'Upload & Index'}
            </button>
          </div>
          {selectedFile && (
            <div className={`rounded-2xl border px-4 py-3 text-sm ${dark ? 'border-white/10 bg-white/5' : 'border-[#D3CBB8] bg-[#FAF8F5]'}`}>
              <span className="font-semibold">{selectedFile.name}</span>
              <span className={`ml-2 ${dark ? 'text-slate-400' : 'text-stone-500'}`}>({formatFileSize(selectedFile.size)})</span>
            </div>
          )}
          {uploadResult && (
            <div className={`rounded-2xl border px-4 py-3 text-sm ${uploadResult.success ? 'border-emerald-400/30 bg-emerald-500/10 text-emerald-300' : 'border-amber-400/30 bg-amber-500/10 text-amber-300'}`}>
              {uploadResult.success ? '\u2705 ' + uploadResult.message : '\u274C ' + (uploadResult.error || 'Upload failed.')}
            </div>
          )}
        </div>
      </ResultCard>

      {status && (
        <div className={`rounded-2xl border px-4 py-3 text-sm ${dark ? 'border-white/10 bg-white/5 text-slate-300' : 'border-[#D3CBB8] bg-[#FAF8F5] text-stone-600'}`}>
          <span className="font-semibold">Status:</span>{' '}
          {status.has_documents ? (
            <>
              {status.total_chunks} chunks indexed from <span className="font-medium">{status.document_names.join(', ')}</span>
              {' | '}Embedding: {status.embedding_backend}
              {' | '}LLM: {status.llm_backend}
            </>
          ) : (
            'No documents uploaded yet.'
          )}
          {status.has_documents && (
            <button type="button" onClick={handleClear} disabled={clearing} className="ml-3 rounded-xl border border-red-400/30 px-3 py-1 text-xs font-medium text-red-400 hover:bg-red-500/10 disabled:opacity-50">
              {clearing ? 'Clearing...' : 'Clear'}
            </button>
          )}
        </div>
      )}

      <ResultCard title="Ask About Organization Documents" subtitle="Ask questions in natural language. Answers are strictly based on uploaded documents." theme={theme}
        actions={
          <button type="button" onClick={handleAsk} disabled={asking || !question.trim()} className={`rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${dark ? 'bg-cyan-400 text-slate-950 hover:bg-cyan-300' : 'bg-clay text-white hover:bg-clay/90'}`}>
            {asking ? 'Thinking...' : 'Ask'}
          </button>
        }
      >
        <textarea value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="e.g., What is the dress code on Mondays?" rows={2}
          className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none transition resize-none ${dark ? 'border-white/10 bg-slate-950/70 text-slate-50 placeholder:text-slate-500 focus:border-cyan-400/40' : 'border-[#D3CBB8] bg-[#FAF8F5] text-stone-850 placeholder:text-stone-400 focus:border-clay'}`}
        />
        {error && (
          <div className="mt-3 rounded-2xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">{error}</div>
        )}
      </ResultCard>

      {answer && (
  <ResultCard
    title="Answer"
    subtitle="Generated from organization documents"
    theme={theme}
  >
    <div className="space-y-3">
      <div
        className={`rounded-2xl border p-4 leading-7 ${
          answer.found
            ? dark
              ? 'border-emerald-400/30 bg-emerald-500/10'
              : 'border-emerald-400/20 bg-emerald-50'
            : dark
            ? 'border-amber-400/30 bg-amber-500/10'
            : 'border-amber-400/20 bg-amber-50'
        }`}
      >
        <div
          className={`mb-2 text-sm font-semibold ${
            answer.found
              ? dark
                ? 'text-emerald-400'
                : 'text-emerald-700'
              : dark
              ? 'text-amber-400'
              : 'text-amber-700'
          }`}
        >
          {answer.found
            ? 'Found in documents'
            : 'Not found in documents'}
        </div>

        <div
          className={`whitespace-pre-wrap text-sm ${
            dark ? 'text-slate-200' : 'text-stone-800'
          }`}
        >
          {answer.answer}
        </div>
      </div>

      {answer.context_used && (
        <details
          className={`rounded-2xl border p-3 text-xs ${
            dark
              ? 'border-white/10 bg-white/5'
              : 'border-[#D3CBB8] bg-[#FAF8F5]'
          }`}
        >
          <summary
            className={`cursor-pointer font-semibold ${
              dark ? 'text-slate-400' : 'text-stone-500'
            }`}
          >
            View Retrieved Context ({answer.context_used.length} chars)
          </summary>

          <pre
            className={`mt-2 max-h-60 overflow-auto whitespace-pre-wrap break-words ${
              dark ? 'text-slate-400' : 'text-stone-500'
            }`}
          >
            {answer.context_used}
          </pre>
        </details>
      )}
    </div>
  </ResultCard>
)}
    </div>
  )
}
