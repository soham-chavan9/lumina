'use client'

import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import FileUpload from '../components/FileUpload'
import ChatBox from '../components/ChatBox'
import ResponseCard from '../components/ResponseCard'
import DocumentLibrary from '../components/DocumentLibrary'
import SuggestedQuestions from '../components/SuggestedQuestions'
import RiskScan from '../components/RiskScan'
import BreachClock from '../components/BreachClock'
import AccessRequestGuide from '../components/AccessRequestGuide'
import BaaScreen from '../components/BaaScreen'
import PhiScan from '../components/PhiScan'
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
      setSuggestions([])
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
      toast.success('Exposure brief ready')
    } catch (err) {
      setScanError(getErrorMessage(err, 'Exposure brief failed'))
    } finally {
      setScanLoading(false)
    }
  }

  const hasCorpus = documents.length > 0

  return (
    <div className="desk-shell">
      <header className="desk-nav">
        <div className="mx-auto flex max-w-[1080px] items-center justify-between px-5 py-3 md:px-8">
          <a href="#top" className="flex items-center gap-2.5 no-underline">
            <span className="mark" aria-hidden>
              L
            </span>
            <span className="text-[17px] font-semibold tracking-[-0.02em] text-[var(--ink)]">
              Lumina
            </span>
          </a>

          <div className="flex items-center gap-2">
            <span className="pill">
              <span
                className={`status-dot ${
                  apiStatus === 'online' ? '' : apiStatus === 'checking' ? 'warn' : 'bad'
                }`}
              />
              {apiStatus === 'online'
                ? 'Online'
                : apiStatus === 'checking'
                  ? 'Connecting'
                  : 'Offline'}
            </span>
            <span className="pill hidden tabular-nums sm:inline-flex">{documents.length} filed</span>
            {modelName ? <span className="pill hidden md:inline-flex">{modelName}</span> : null}
          </div>
        </div>
      </header>

      <main id="top" className="mx-auto max-w-[1080px] px-5 pb-28 pt-8 md:px-8 md:pt-12">
        <section className="hero-stage desk-rise relative mb-14 px-7 py-10 md:px-12 md:py-14">
          <div className="relative z-10 max-w-xl">
            <p className="desk-kicker">HIPAA privacy desk</p>
            <h1 className="mt-3 text-[clamp(2.6rem,6vw,4.25rem)] leading-[1.02] tracking-[-0.045em] text-[var(--ink)]">
              Lumina
            </h1>
            <p className="mt-4 max-w-md text-[17px] leading-relaxed text-[var(--ink-soft)]">
              File your policies once. Ask with citations. Run the breach, access, and BAA
              workflows Privacy Officers use every week.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <a href="#corpus" className="desk-btn desk-btn-primary no-underline">
                File policies
              </a>
              <a href="#workflows" className="desk-btn desk-btn-ghost no-underline">
                Open workflows
              </a>
            </div>
            <p className="mt-6 max-w-md text-[12px] leading-relaxed text-[var(--faint)]">
              Not legal advice and not a substitute for your Privacy Officer, Security Officer, or
              counsel. Outputs may be degraded when models are unavailable — confirm before acting.
              Workflow narratives may be sent to your configured model provider when you acknowledge
              export.
            </p>
          </div>
          <div className="hero-orb hidden md:block" aria-hidden />
        </section>

        {apiStatus === 'offline' && (
          <div className="desk-rise mb-8 rounded-[16px] border border-[rgba(255,59,48,0.2)] bg-[rgba(255,59,48,0.06)] px-4 py-3.5 text-sm text-[var(--bad)]">
            Cannot reach the Lumina API. Start the backend on port 8000, then refresh.
          </div>
        )}

        <div id="corpus" className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="desk-rise-delay space-y-5">
            <FileUpload onUploadComplete={handleUploadComplete} />
            <DocumentLibrary
              documents={documents}
              totalChunks={totalChunks}
              loading={libraryLoading}
              clearing={clearing}
              onClear={() => void handleClear()}
            />
          </div>

          <div className="space-y-5">
            <section className="desk-panel p-6 md:p-7">
              <p className="desk-kicker">Ask</p>
              <h2 className="section-title mt-1">Ask the HIPAA corpus</h2>
              <p className="mt-2 mb-6 text-[15px] leading-relaxed text-[var(--muted)]">
                Replace guesswork with cited findings from your NPP, IRP, and workforce procedures.
              </p>
              <ChatBox
                onResponseGenerated={handleNewResponse}
                draftQuestion={draftQuestion}
                onDraftConsumed={() => setDraftQuestion(undefined)}
                disabled={!hasCorpus || apiStatus === 'offline'}
              />
              {hasCorpus && (
                <div className="mt-6">
                  <SuggestedQuestions
                    suggestions={suggestions}
                    loading={suggestionsLoading}
                    onSelect={setDraftQuestion}
                    disabled={apiStatus === 'offline'}
                  />
                </div>
              )}
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

        <div id="workflows" className="mt-16 mb-6 desk-fade">
          <p className="desk-kicker">Daily operations</p>
          <h2 className="section-title mt-1">Privacy workflows</h2>
          <p className="mt-2 max-w-xl text-[15px] text-[var(--muted)]">
            Breach clocks, individual rights, and Business Associate diligence — grounded in your
            filed policies when available.
          </p>
        </div>

        <div className="grid gap-5">
          <BreachClock disabled={apiStatus === 'offline'} />
          <AccessRequestGuide disabled={apiStatus === 'offline'} />
          <BaaScreen disabled={apiStatus === 'offline'} />
          <PhiScan disabled={apiStatus === 'offline'} />
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
