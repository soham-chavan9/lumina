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
    <section className="desk-panel p-6 md:p-7">
      <div className="mb-5 flex items-start justify-between gap-3">
        <div>
          <p className="desk-kicker">Library</p>
          <h2 className="section-title mt-1 text-[1.65rem]">Active corpus</h2>
          <p className="mt-1.5 text-[14px] tabular-nums text-[var(--muted)]">
            {totalChunks === 1 ? '1 searchable passage' : `${totalChunks} searchable passages`}
          </p>
        </div>
        <button
          type="button"
          className="desk-btn desk-btn-ghost px-3 py-2 text-sm"
          onClick={onClear}
          disabled={!documents.length || clearing}
          aria-label="Clear corpus"
        >
          {clearing ? <Loader2 size={15} className="animate-spin" /> : <Trash2 size={15} />}
          Clear
        </button>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-sm text-[var(--muted)]">
          <Loader2 size={15} className="animate-spin" /> Loading…
        </div>
      ) : documents.length === 0 ? (
        <div className="rounded-[16px] bg-[rgba(0,0,0,0.03)] px-4 py-10 text-center">
          <FileText className="mx-auto mb-2 text-[var(--faint)]" size={22} strokeWidth={1.5} />
          <p className="text-[15px] font-semibold text-[var(--ink)]">Nothing filed yet</p>
          <p className="mt-1 text-[14px] text-[var(--muted)]">
            Add a policy PDF to unlock ask and exposure brief.
          </p>
        </div>
      ) : (
        <ul className="space-y-2">
          {documents.map((doc) => (
            <li
              key={doc.source}
              className="flex items-center gap-3 rounded-[14px] bg-[rgba(0,0,0,0.03)] px-3.5 py-3"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] bg-[var(--accent-soft)] text-[var(--accent)]">
                <FileText size={15} />
              </span>
              <div className="min-w-0">
                <p className="truncate text-[14px] font-semibold tracking-[-0.01em] text-[var(--ink)]">
                  {doc.source}
                </p>
                <p className="text-[12px] tabular-nums text-[var(--faint)]">
                  {doc.chunks} passage{doc.chunks === 1 ? '' : 's'}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
