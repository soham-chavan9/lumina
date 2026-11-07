'use client'

import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { AxiosError } from 'axios'
import FileUpload from '../components/FileUpload'
import ChatBox from '../components/ChatBox'
import ResponseCard from '../components/ResponseCard'
import DocumentLibrary from '../components/DocumentLibrary'
import SuggestedQuestions from '../components/SuggestedQuestions'
import RiskScan from '../components/RiskScan'
import {
  clearDocuments,
  fetchDocuments,
  fetchSuggestions,
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
          question: 'What personal data does this policy cover?',
          category: 'privacy',
        },
        {
          question: 'What are the data breach notification requirements?',
          category: 'incident',
        },
      ])
    } finally {
      setSuggestionsLoading(false)
    }
  }, [])

  useEffect(() => {
    void refreshLibrary()
    void refreshSuggestions()
  }, [refreshLibrary, refreshSuggestions])

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
      toast.success('Library cleared')
      void refreshSuggestions()
    } catch {
      toast.error('Could not clear library')
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
    setResponses((prev) => [
      { question, answer, sources, citation, confidence },
      ...prev,
    ])
  }

  const handleScan = async () => {
    setScanLoading(true)
    setScanError(null)
    try {
      const result = await runRiskScan()
      setScanResult(result)
      toast.success('Risk scan ready')
    } catch (err) {
      const ax = err as AxiosError<{ detail?: string }>
      setScanError(
        ax.response?.data?.detail || ax.message || 'Scan failed. Check API quota.'
      )
    } finally {
      setScanLoading(false)
    }
  }

  return (
    <div className="min-h-screen">
      <header className="lumina-glass sticky top-0 z-20">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3.5 md:px-8">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-[var(--lumina-blue)] text-sm font-bold text-white shadow-[0_6px_16px_rgba(0,113,227,0.35)]">
              L
            </span>
            <div>
              <p className="text-[15px] font-semibold tracking-tight text-[var(--lumina-ink)]">
                Lumina
              </p>
              <p className="text-[11px] text-[var(--lumina-faint)]">Compliance Intelligence</p>
            </div>
          </div>
          <div className="hidden items-center gap-2 text-xs text-[var(--lumina-muted)] sm:flex">
            <span className="rounded-full bg-[rgba(0,0,0,0.04)] px-2.5 py-1 tabular-nums">
              {documents.length} doc{documents.length === 1 ? '' : 's'}
            </span>
            <span className="rounded-full bg-[rgba(0,0,0,0.04)] px-2.5 py-1 tabular-nums">
              {totalChunks} chunks
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 pb-20 pt-10 md:px-8">
        <section className="lumina-enter mb-10 max-w-3xl">
          <p className="text-[13px] font-semibold uppercase tracking-[0.12em] text-[var(--lumina-faint)]">
            Policy Q&A
          </p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight text-[var(--lumina-ink)] md:text-5xl">
            Lumina
          </h1>
          <p className="mt-3 max-w-2xl text-lg leading-relaxed text-[var(--lumina-muted)]">
            Upload compliance PDFs, ask precise questions with citations, and scan for risk — in a
            calm, Apple-inspired workspace.
          </p>
        </section>

        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
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
            <section className="lumina-panel p-5 md:p-6">
              <p className="text-[13px] font-semibold uppercase tracking-[0.08em] text-[var(--lumina-faint)]">
                Ask
              </p>
              <h2 className="mt-1 text-[22px] font-semibold tracking-tight">Grounded answers</h2>
              <p className="mt-1 mb-5 text-sm text-[var(--lumina-muted)]">
                Answers stay tied to retrieved policy chunks — with citation and confidence.
              </p>
              <ChatBox
                onResponseGenerated={handleNewResponse}
                draftQuestion={draftQuestion}
                onDraftConsumed={() => setDraftQuestion(undefined)}
              />
              <div className="mt-5">
                <SuggestedQuestions
                  suggestions={suggestions}
                  loading={suggestionsLoading}
                  onSelect={setDraftQuestion}
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
            disabled={documents.length === 0}
          />
        </div>
      </main>
    </div>
  )
}
