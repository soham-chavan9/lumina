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
      className="desk-panel overflow-hidden p-5 md:p-6"
    >
      <p className="desk-kicker">Inquiry</p>
      <p className="mt-2 text-[0.98rem] leading-relaxed text-[var(--ink)]">{question}</p>

      <hr className="desk-rule" />

      <div className="flex items-center justify-between gap-3">
        <p className="desk-kicker" style={{ color: 'var(--signal)' }}>
          Finding
        </p>
        {confidence && (
          <span className="rounded-full bg-[rgba(20,24,31,0.05)] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--muted)]">
            {confidence} confidence
          </span>
        )}
      </div>
      <p className="mt-2 text-[0.98rem] leading-relaxed text-[var(--ink)]">{answer}</p>

      {citation && (
        <div className="mt-4 rounded-[14px] border-l-[3px] border-[var(--teal)] bg-[var(--teal-soft)] px-3.5 py-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[var(--teal)]">
            Citation
          </p>
          <p className="mt-1 text-sm leading-relaxed text-[var(--ink-soft)]">{citation}</p>
        </div>
      )}

      {sources.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {sources.map((src) => (
            <span
              key={src}
              className="rounded-full border border-[var(--line)] bg-white px-2.5 py-1 text-xs text-[var(--muted)]"
            >
              {src}
            </span>
          ))}
        </div>
      )}
    </motion.article>
  )
}
