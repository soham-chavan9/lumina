'use client'

import { FormEvent, useEffect, useState } from 'react'
import { ArrowUp, Loader2 } from 'lucide-react'
import { askQuestion } from '../lib/api'

type Props = {
  onResponseGenerated: (
    question: string,
    answer: string,
    sources: string[],
    citation?: string,
    confidence?: string
  ) => void
  draftQuestion?: string
  onDraftConsumed?: () => void
}

export default function ChatBox({
  onResponseGenerated,
  draftQuestion,
  onDraftConsumed,
}: Props) {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!draftQuestion) return
    setQuestion(draftQuestion)
    onDraftConsumed?.()
  }, [draftQuestion, onDraftConsumed])

  const submit = async (value: string) => {
    const q = value.trim()
    if (!q || loading) return
    setLoading(true)
    setError(null)
    try {
      const data = await askQuestion(q)
      const sources =
        data.sources?.length
          ? data.sources
          : (data.source_documents || []).map((s) =>
              typeof s === 'string' ? s : s.source
            )
      onResponseGenerated(
        q,
        data.answer,
        sources,
        data.citation,
        data.confidence
      )
      setQuestion('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get a response.')
    } finally {
      setLoading(false)
    }
  }

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    void submit(question)
  }

  return (
    <div>
      <form onSubmit={onSubmit} className="relative">
        <input
          className="lumina-input pr-14"
          placeholder="Ask about privacy, breaches, consent, or controls…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={loading}
          aria-label="Ask Lumina"
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="absolute right-2 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-[var(--lumina-blue)] text-white transition hover:bg-[#0077ed] disabled:opacity-40"
          aria-label="Send question"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <ArrowUp size={16} />}
        </button>
      </form>
      {error && <p className="mt-2 text-center text-sm text-[var(--lumina-red)]">{error}</p>}
    </div>
  )
}
