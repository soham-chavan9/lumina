'use client'

import { FormEvent, useEffect, useState } from 'react'
import { ArrowUp, Loader2 } from 'lucide-react'
import { askQuestion, getErrorMessage } from '../lib/api'

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
  disabled?: boolean
}

export default function ChatBox({
  onResponseGenerated,
  draftQuestion,
  onDraftConsumed,
  disabled,
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
    if (!q || loading || disabled) return
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
      onResponseGenerated(q, data.answer, sources, data.citation, data.confidence)
      setQuestion('')
    } catch (err) {
      setError(getErrorMessage(err, 'Could not retrieve an answer.'))
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
          className="desk-input pr-14"
          placeholder={
            disabled
              ? 'File a HIPAA policy before asking…'
              : 'Ask about breach notice, access rights, BAAs…'
          }
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={loading || disabled}
          aria-label="Ask the corpus"
        />
        <button
          type="submit"
          disabled={loading || disabled || !question.trim()}
          className="absolute right-1.5 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-[var(--accent)] text-white transition hover:bg-[var(--accent-deep)] disabled:opacity-35"
          aria-label="Send question"
        >
          {loading ? <Loader2 size={15} className="animate-spin" /> : <ArrowUp size={15} />}
        </button>
      </form>
      {error && <p className="mt-2.5 text-center text-sm text-[var(--bad)]">{error}</p>}
    </div>
  )
}
