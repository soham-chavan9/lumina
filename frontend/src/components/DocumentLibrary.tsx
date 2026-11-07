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
    <section className="desk-panel p-5 md:p-6">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="desk-kicker">Dossier</p>
          <h2 className="mt-1 text-[1.45rem] text-[var(--ink)]">Active corpus</h2>
          <p className="mt-1 text-sm tabular-nums text-[var(--muted)]">
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
          <Loader2 size={15} className="animate-spin" /> Reading dossier…
        </div>
      ) : documents.length === 0 ? (
        <div className="rounded-[14px] border border-dashed border-[var(--line)] px-4 py-8 text-center">
          <FileText className="mx-auto mb-2 text-[var(--faint)]" size={20} />
          <p className="text-sm font-semibold text-[var(--ink)]">Desk is empty</p>
          <p className="mt-1 text-sm text-[var(--muted)]">
            File a policy PDF to unlock interrogation and exposure review.
          </p>
        </div>
      ) : (
        <ul className="space-y-2">
          {documents.map((doc) => (
            <li
              key={doc.source}
              className="flex items-center gap-3 rounded-[14px] bg-[rgba(20,24,31,0.03)] px-3.5 py-3"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--teal-soft)] text-[var(--teal)]">
                <FileText size={15} />
              </span>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-[var(--ink)]">{doc.source}</p>
                <p className="text-xs tabular-nums text-[var(--faint)]">
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
