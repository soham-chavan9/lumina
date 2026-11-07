'use client'

import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import FileUpload from '../components/FileUpload'
import ChatBox from '../components/ChatBox'
import ResponseCard from '../components/ResponseCard'
import DocumentLibrary from '../components/DocumentLibrary'
import SuggestedQuestions from '../components/SuggestedQuestions'
import RiskScan from '../components/RiskScan'
import {
  clearDocuments,
  fetchDocuments,
  fetchHealth,
  fetchSuggestions,
  getErrorMessage,
  runRiskScan,
  type DocumentInfo,
  type RiskScanResponse,
  type SuggestionItem,
} from '../lib/api'

type ChatItem = {
  question: string
  answer: string
  sources: string[]
  citation?: string
  confidence?: string
}

type ApiStatus = 'checking' | 'online' | 'offline'

export default function HomePage() {
  const [responses, setResponses] = useState<ChatItem[]>([])
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [totalChunks, setTotalChunks] = useState(0)
  const [libraryLoading, setLibraryLoading] = useState(true)
  const [clearing, setClearing] = useState(false)
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([])
  const [suggestionsLoading, setSuggestionsLoading] = useState(true)
  const [draftQuestion, setDraftQuestion] = useState<string | undefined>()
  const [scanResult, setScanResult] = useState<RiskScanResponse | null>(null)
  const [scanLoading, setScanLoading] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking')
  const [modelName, setModelName] = useState<string>('')

  const refreshLibrary = useCallback(async () => {
    setLibraryLoading(true)
    try {
      const data = await fetchDocuments()
      setDocuments(data.documents)
      setTotalChunks(data.total_chunks)
    } catch {
      /* keep previous */
    } finally {
      setLibraryLoading(false)
    }
  }, [])

  const refreshSuggestions = useCallback(async () => {
    setSuggestionsLoading(true)
    try {
      const items = await fetchSuggestions()
      setSuggestions(items)
    } catch {
      setSuggestions([
        {
          question: 'Which personal data categories does this policy admit processing?',
          category: 'privacy',
        },
        {
          question: 'What is the breach notification timeline for affected persons?',
          category: 'incident',
        },
        {
          question: 'How does a data subject withdraw consent in practice?',
          category: 'rights',
        },
        {
          question: 'Who owns escalation when a control fails?',
          category: 'governance',
        },
      ])
    } finally {
      setSuggestionsLoading(false)
    }
  }, [])

  const pingHealth = useCallback(async () => {
    try {
      const health = await fetchHealth()
      setApiStatus('online')
      setModelName(health.model)
    } catch {
      setApiStatus('offline')
    }
  }, [])

  useEffect(() => {
    void pingHealth()
    void refreshLibrary()
    void refreshSuggestions()
  }, [pingHealth, refreshLibrary, refreshSuggestions])

  const handleUploadComplete = () => {
    void refreshLibrary()
    void refreshSuggestions()
    setScanResult(null)
    setScanError(null)
  }

  const handleClear = async () => {
    setClearing(true)
    try {
      await clearDocuments()
      setDocuments([])
      setTotalChunks(0)
      setResponses([])
      setScanResult(null)
      toast.success('Corpus cleared')
      void refreshSuggestions()
    } catch (err) {
      toast.error(getErrorMessage(err, 'Could not clear corpus'))
    } finally {
      setClearing(false)
    }
  }

  const handleNewResponse = (
    question: string,
    answer: string,
    sources: string[],
    citation?: string,
    confidence?: string
  ) => {
    setResponses((prev) => [{ question, answer, sources, citation, confidence }, ...prev])
  }

  const handleScan = async () => {
    setScanLoading(true)
    setScanError(null)
    try {
      const result = await runRiskScan()
      setScanResult(result)
      toast.success('Exposure review ready')
    } catch (err) {
      setScanError(getErrorMessage(err, 'Exposure review failed'))
    } finally {
      setScanLoading(false)
    }
  }

  const hasCorpus = documents.length > 0

  return (
    <div className="desk-shell">
      <header className="desk-nav">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3.5 md:px-8">
          <div className="flex items-center gap-3">
            <span className="mark" aria-hidden>
              L
            </span>
            <div>
              <p className="font-[family-name:var(--font-display)] text-[1.15rem] leading-none text-[var(--ink)]">
                Lumina
              </p>
              <p className="mt-1 text-[11px] tracking-[0.04em] text-[var(--faint)]">
                Policy interrogation desk
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs text-[var(--muted)]">
            <span className="inline-flex items-center gap-2 rounded-full border border-[var(--line)] bg-white/70 px-2.5 py-1">
              <span
                className={`status-dot ${
                  apiStatus === 'online' ? '' : apiStatus === 'checking' ? 'warn' : 'bad'
                }`}
              />
              {apiStatus === 'online'
                ? 'Desk online'
                : apiStatus === 'checking'
                  ? 'Connecting…'
                  : 'API offline'}
            </span>
            <span className="hidden rounded-full border border-[var(--line)] bg-white/70 px-2.5 py-1 tabular-nums sm:inline">
              {documents.length} filed
            </span>
            {modelName && (
              <span className="hidden rounded-full border border-[var(--line)] bg-white/70 px-2.5 py-1 md:inline">
                {modelName}
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 pb-24 pt-10 md:px-8">
        <section className="desk-rise mb-10 max-w-3xl">
          <p className="desk-kicker">Compliance workspace</p>
          <h1 className="mt-3 text-[2.75rem] leading-[1.05] text-[var(--ink)] md:text-[3.4rem]">
            Lumina
          </h1>
          <p className="mt-4 max-w-2xl text-[1.05rem] leading-relaxed text-[var(--ink-soft)]">
            A quiet desk for serious policy work — file the corpus, press it with precise
            questions, and leave with cited findings plus an exposure brief.
          </p>
        </section>

        {apiStatus === 'offline' && (
          <div className="desk-rise mb-6 rounded-[14px] border border-[rgba(159,18,57,0.25)] bg-[rgba(159,18,57,0.06)] px-4 py-3 text-sm text-[var(--bad)]">
            Cannot reach the Lumina API. Start the backend on port 8000, then refresh.
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[0.92fr_1.08fr]">
          <div className="space-y-6">
            <FileUpload onUploadComplete={handleUploadComplete} />
            <DocumentLibrary
              documents={documents}
              totalChunks={totalChunks}
              loading={libraryLoading}
              clearing={clearing}
              onClear={() => void handleClear()}
            />
          </div>

          <div className="space-y-6">
            <section className="desk-panel p-5 md:p-6">
              <p className="desk-kicker">Interrogation</p>
              <h2 className="mt-1 text-[1.45rem] text-[var(--ink)]">Ask the corpus</h2>
              <p className="mt-1 mb-5 text-sm leading-relaxed text-[var(--muted)]">
                Answers refuse to invent. Every finding is bound to retrieved passages, a
                citation, and a confidence call.
              </p>
              <ChatBox
                onResponseGenerated={handleNewResponse}
                draftQuestion={draftQuestion}
                onDraftConsumed={() => setDraftQuestion(undefined)}
                disabled={!hasCorpus || apiStatus === 'offline'}
              />
              <div className="mt-5">
                <SuggestedQuestions
                  suggestions={suggestions}
                  loading={suggestionsLoading}
                  onSelect={setDraftQuestion}
                  disabled={!hasCorpus || apiStatus === 'offline'}
                />
              </div>
            </section>

            {responses.length > 0 && (
              <div className="space-y-4">
                {responses.map((res, idx) => (
                  <ResponseCard
                    key={`${res.question}-${idx}`}
                    question={res.question}
                    answer={res.answer}
                    sources={res.sources}
                    citation={res.citation}
                    confidence={res.confidence}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="mt-6">
          <RiskScan
            result={scanResult}
            loading={scanLoading}
            error={scanError}
            onScan={() => void handleScan()}
            disabled={!hasCorpus || apiStatus === 'offline'}
          />
        </div>
      </main>
    </div>
  )
}
