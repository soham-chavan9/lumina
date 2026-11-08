'use client'

import type { SuggestionItem } from '../lib/api'

type Props = {
  suggestions: SuggestionItem[]
  loading?: boolean
  onSelect: (question: string) => void
  disabled?: boolean
}

export default function SuggestedQuestions({
  suggestions,
  loading,
  onSelect,
  disabled,
}: Props) {
  return (
    <section>
      <p className="desk-kicker mb-3">Suggested</p>
      {loading ? (
        <p className="text-sm text-[var(--muted)]">Preparing probes…</p>
      ) : (
        <div className="grid gap-2 sm:grid-cols-2">
          {suggestions.map((item) => (
            <button
              key={item.question}
              type="button"
              className="desk-chip"
              disabled={disabled}
              onClick={() => onSelect(item.question)}
            >
              <span>{item.category}</span>
              <strong>{item.question}</strong>
            </button>
          ))}
        </div>
      )}
    </section>
  )
}
