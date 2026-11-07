'use client'

import { Sparkles } from 'lucide-react'
import type { SuggestionItem } from '../lib/api'

type Props = {
  suggestions: SuggestionItem[]
  loading?: boolean
  onSelect: (question: string) => void
}

export default function SuggestedQuestions({ suggestions, loading, onSelect }: Props) {
  return (
    <section className="lumina-enter">
      <div className="mb-3 flex items-center gap-2">
        <Sparkles size={16} className="text-[var(--lumina-blue)]" />
        <h3 className="text-sm font-semibold text-[var(--lumina-ink)]">Suggested questions</h3>
      </div>
      {loading ? (
        <p className="text-sm text-[var(--lumina-muted)]">Preparing questions…</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {suggestions.map((item) => (
            <button
              key={item.question}
              type="button"
              className="lumina-chip"
              onClick={() => onSelect(item.question)}
            >
              <span className="mr-2 text-[11px] uppercase tracking-wide text-[var(--lumina-faint)]">
                {item.category}
              </span>
              {item.question}
            </button>
          ))}
        </div>
      )}
    </section>
  )
}
