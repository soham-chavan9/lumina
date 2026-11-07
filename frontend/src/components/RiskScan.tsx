'use client'

import { Loader2, ScanSearch } from 'lucide-react'
import type { RiskScanResponse } from '../lib/api'

type Props = {
  result: RiskScanResponse | null
  loading?: boolean
  error?: string | null
  onScan: () => void
  disabled?: boolean
}

const severityColor: Record<string, string> = {
  High: 'var(--bad)',
  Medium: 'var(--warn)',
  Low: 'var(--ok)',
}

export default function RiskScan({ result, loading, error, onScan, disabled }: Props) {
  return (
    <section className="desk-panel p-5 md:p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="desk-kicker">OCR readiness</p>
          <h2 className="mt-1 text-[1.45rem] text-[var(--ink)]">HIPAA exposure brief</h2>
          <p className="mt-1 max-w-xl text-sm leading-relaxed text-[var(--muted)]">
            Scan filed policies for gaps OCR cares about — breach readiness, access rights,
            BAAs/vendors, minimum necessary, and sanctions — with next actions attached.
          </p>
        </div>
        <button
          type="button"
          className="desk-btn desk-btn-primary"
          onClick={onScan}
          disabled={disabled || loading}
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <ScanSearch size={16} />}
          {loading ? 'Reviewing…' : 'Run HIPAA exposure brief'}
        </button>
      </div>

      {error && (
        <p className="mb-3 rounded-[12px] bg-[rgba(159,18,57,0.08)] px-3 py-2 text-sm text-[var(--bad)]">
          {error}
        </p>
      )}

      {!result && !loading && !error && (
        <div className="rounded-[14px] border border-dashed border-[var(--line)] px-4 py-8 text-center text-sm text-[var(--muted)]">
          File HIPAA policies, then run an OCR-minded exposure brief.
        </div>
      )}

      {result && (
        <div className="desk-rise space-y-4">
          <p className="text-[0.98rem] leading-relaxed text-[var(--ink)]">{result.summary}</p>

          {result.findings.length > 0 && (
            <div className="space-y-2">
              {result.findings.map((finding) => (
                <article
                  key={`${finding.title}-${finding.severity}`}
                  className="rounded-[14px] border border-[var(--line)] bg-white p-4"
                >
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <h4 className="font-[family-name:var(--font-display)] text-[1.02rem] text-[var(--ink)]">
                      {finding.title}
                    </h4>
                    <span
                      className="text-[11px] font-semibold uppercase tracking-[0.08em]"
                      style={{ color: severityColor[finding.severity] || 'inherit' }}
                    >
                      {finding.severity}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed text-[var(--muted)]">{finding.detail}</p>
                  {finding.recommendation && (
                    <p className="mt-2 text-sm text-[var(--ink)]">
                      <span className="font-semibold text-[var(--teal)]">Action · </span>
                      {finding.recommendation}
                    </p>
                  )}
                </article>
              ))}
            </div>
          )}

          {result.strengths.length > 0 && (
            <div>
              <p className="desk-kicker mb-2">Residual strengths</p>
              <ul className="space-y-1.5">
                {result.strengths.map((item) => (
                  <li key={item} className="text-sm text-[var(--ink-soft)]">
                    — {item}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
