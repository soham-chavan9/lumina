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
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="desk-panel overflow-hidden p-6 md:p-7"
    >
      <p className="desk-kicker">Question</p>
      <p className="mt-2 text-[15px] leading-relaxed tracking-[-0.01em] text-[var(--ink)]">
        {question}
      </p>

      <hr className="desk-rule" />

      <div className="flex items-center justify-between gap-3">
        <p className="desk-kicker">Answer</p>
        {confidence && (
          <span className="pill tabular-nums">{confidence} confidence</span>
        )}
      </div>
      <p className="mt-2 text-[15px] leading-relaxed text-[var(--ink)]">{answer}</p>

      {citation && (
        <div className="mt-5 rounded-[14px] bg-[var(--accent-soft)] px-4 py-3.5">
          <p className="text-[12px] font-semibold tracking-[-0.01em] text-[var(--accent)]">
            Citation
          </p>
          <p className="mt-1 text-[14px] leading-relaxed text-[var(--ink-soft)]">{citation}</p>
        </div>
      )}

      {sources.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {sources.map((src) => (
            <span key={src} className="pill">
              {src}
            </span>
          ))}
        </div>
      )}
    </motion.article>
  )
}
