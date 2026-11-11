'use client'

import { FormEvent, useState } from 'react'
import { FileSearch, Loader2, ShieldAlert, ShieldCheck } from 'lucide-react'
import { getErrorMessage, runPhiScan, type PhiScanResponse } from '../lib/api'

type Props = { disabled?: boolean }

export default function PhiScan({ disabled }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PhiScanResponse | null>(null)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!file || disabled || loading) return
    setLoading(true)
    setError(null)
    try {
      setResult(await runPhiScan(file))
    } catch (err) {
      setResult(null)
      setError(getErrorMessage(err, 'PHI scan failed'))
    } finally {
      setLoading(false)
    }
  }

  const plural = result && result.identifier_count === 1 ? '' : 's'

  return (
    <section className="desk-panel p-6 md:p-7">
      <p className="desk-kicker">De-identification</p>
      <h2 className="section-title mt-1 text-[1.65rem]">PHI scan</h2>
      <p className="mt-2 text-[15px] leading-relaxed text-[var(--muted)]">
        Check a document for HIPAA Safe Harbor identifiers before it is shared or filed. Runs on
        this server; nothing is stored or sent to a model provider.
      </p>

      <form onSubmit={onSubmit} className="mt-5 flex flex-wrap items-center gap-3">
        <input
          type="file"
          accept="application/pdf"
          aria-label="PDF to scan for PHI"
          className="desk-field max-w-sm"
          disabled={disabled || loading}
          onChange={(e) => {
            setFile(e.target.files?.[0] ?? null)
            setResult(null)
            setError(null)
          }}
        />
        <button type="submit" className="desk-btn desk-btn-primary" disabled={disabled || loading || !file}>
          {loading ? <Loader2 size={16} className="animate-spin" /> : <FileSearch size={16} />}
          {loading ? 'Scanning…' : 'Scan for PHI'}
        </button>
      </form>

      {error && (
        <p className="mt-4 rounded-[12px] bg-[rgba(255,59,48,0.08)] px-3.5 py-2.5 text-sm text-[var(--bad)]">
          {error}
        </p>
      )}

      {result && (
        <div className="desk-rise mt-6 space-y-5 border-t border-[var(--line)] pt-5">
          {result.verdict === 'phi_found' ? (
            <p className="flex items-start gap-2 rounded-[12px] bg-[rgba(255,59,48,0.08)] px-3.5 py-2.5 text-[14px] text-[var(--bad)]">
              <ShieldAlert size={16} className="mt-0.5 shrink-0" />
              <span>
                {result.identifier_count} PHI identifier{plural} found in {result.filename}.{' '}
                {result.likely_patient_record
                  ? 'This looks like a patient record: keep it out of the policy library and share it only under a BAA or after de-identification.'
                  : 'Review before sharing.'}
              </span>
            </p>
          ) : (
            <p className="flex items-start gap-2 rounded-[12px] bg-[rgba(52,199,89,0.1)] px-3.5 py-2.5 text-[14px] text-[var(--ink)]">
              <ShieldCheck size={16} className="mt-0.5 shrink-0 text-[var(--ok)]" />
              <span>No Safe Harbor identifiers found in {result.filename}.</span>
            </p>
          )}

          {result.categories.length > 0 && (
            <ul className="divide-y divide-[var(--line)] text-[14px]">
              {result.categories.map((c) => (
                <li key={c.category} className="flex flex-wrap items-baseline justify-between gap-2 py-2.5">
                  <span className="text-[var(--ink)]">{c.label}</span>
                  <span className="flex flex-wrap items-center gap-2">
                    {c.examples.map((ex, i) => (
                      <code
                        key={`${c.category}-${i}`}
                        className="rounded-md bg-[rgba(0,0,0,0.05)] px-1.5 py-0.5 text-[12px] text-[var(--ink-soft)]"
                      >
                        {ex}
                      </code>
                    ))}
                    <span className="pill tabular-nums">{c.count}</span>
                  </span>
                </li>
              ))}
            </ul>
          )}

          <p className="text-[12px] leading-relaxed text-[var(--faint)]">{result.note}</p>
        </div>
      )}
    </section>
  )
}
