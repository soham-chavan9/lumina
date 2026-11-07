'use client'

import { FileText, Trash2, Loader2 } from 'lucide-react'
import type { DocumentInfo } from '../lib/api'

type Props = {
  documents: DocumentInfo[]
  totalChunks: number
  loading?: boolean
  clearing?: boolean
  onClear: () => void
}

export default function DocumentLibrary({
  documents,
  totalChunks,
  loading,
  clearing,
  onClear,
}: Props) {
  return (
    <section className="lumina-panel p-5 md:p-6">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="text-[13px] font-semibold uppercase tracking-[0.08em] text-[var(--lumina-faint)]">
            Library
          </p>
          <h2 className="mt-1 text-[22px] font-semibold tracking-tight text-[var(--lumina-ink)]">
            Documents
          </h2>
          <p className="mt-1 text-sm text-[var(--lumina-muted)]">
            {totalChunks === 1 ? '1 indexed chunk' : `${totalChunks} indexed chunks`}
          </p>
        </div>
        <button
          type="button"
          className="lumina-btn lumina-btn-secondary px-3 py-2 text-sm"
          onClick={onClear}
          disabled={!documents.length || clearing}
          aria-label="Clear library"
        >
          {clearing ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
          Clear
        </button>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-sm text-[var(--lumina-muted)]">
          <Loader2 size={16} className="animate-spin" /> Loading library…
        </div>
      ) : documents.length === 0 ? (
        <div className="rounded-[18px] border border-dashed border-[var(--lumina-line)] bg-[rgba(0,0,0,0.015)] px-4 py-8 text-center">
          <FileText className="mx-auto mb-2 text-[var(--lumina-faint)]" size={22} />
          <p className="text-sm font-medium text-[var(--lumina-ink)]">No policies yet</p>
          <p className="mt-1 text-sm text-[var(--lumina-muted)]">
            Upload a PDF to start asking grounded questions.
          </p>
        </div>
      ) : (
        <ul className="space-y-2">
          {documents.map((doc) => (
            <li
              key={doc.source}
              className="flex items-center justify-between gap-3 rounded-[14px] bg-[rgba(0,0,0,0.03)] px-3.5 py-3"
            >
              <div className="min-w-0 flex items-center gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--lumina-blue-soft)] text-[var(--lumina-blue)]">
                  <FileText size={16} />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-[var(--lumina-ink)]">
                    {doc.source}
                  </p>
                  <p className="text-xs tabular-nums text-[var(--lumina-faint)]">
                    {doc.chunks} chunk{doc.chunks === 1 ? '' : 's'}
                  </p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
