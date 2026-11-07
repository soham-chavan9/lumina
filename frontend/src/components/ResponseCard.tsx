'use client'

import { motion } from 'framer-motion'

type Props = {
  question: string
  answer: string
  sources?: string[]
  citation?: string
  confidence?: string
}

export default function ResponseCard({
  question,
  answer,
  sources = [],
  citation,
  confidence,
}: Props) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="lumina-panel overflow-hidden p-5 md:p-6"
    >
      <p className="text-[13px] font-semibold uppercase tracking-[0.08em] text-[var(--lumina-faint)]">
        You
      </p>
      <p className="mt-1 text-[15px] leading-relaxed text-[var(--lumina-ink)]">{question}</p>

      <div className="mt-5 border-t border-[var(--lumina-line)] pt-5">
        <div className="mb-1 flex items-center justify-between gap-3">
          <p className="text-[13px] font-semibold uppercase tracking-[0.08em] text-[var(--lumina-blue)]">
            Lumina
          </p>
          {confidence && (
            <span className="rounded-full bg-[rgba(0,0,0,0.04)] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-[var(--lumina-muted)]">
              {confidence}
            </span>
          )}
        </div>
        <p className="text-[15px] leading-relaxed text-[var(--lumina-ink)]">{answer}</p>
      </div>

      {citation && (
        <div className="mt-4 rounded-[14px] bg-[rgba(0,113,227,0.06)] px-3.5 py-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--lumina-blue)]">
            Citation
          </p>
          <p className="mt-1 text-sm leading-relaxed text-[var(--lumina-ink)]">{citation}</p>
        </div>
      )}

      {sources.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {sources.map((src) => (
            <span
              key={src}
              className="rounded-full bg-[rgba(0,0,0,0.04)] px-2.5 py-1 text-xs text-[var(--lumina-muted)]"
            >
              {src}
            </span>
          ))}
        </div>
      )}
    </motion.article>
  )
}
