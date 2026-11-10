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
    <section className="desk-panel p-6 md:p-7">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="desk-kicker">OCR readiness</p>
          <h2 className="section-title mt-1 text-[1.65rem]">HIPAA exposure brief</h2>
          <p className="mt-2 max-w-xl text-[15px] leading-relaxed text-[var(--muted)]">
            Scan filed policies for gaps OCR cares about — breach readiness, access rights,
            BAAs, minimum necessary, and sanctions.
          </p>
        </div>
        <button
          type="button"
          className="desk-btn desk-btn-primary"
          onClick={onScan}
          disabled={disabled || loading}
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <ScanSearch size={16} />}
          {loading ? 'Reviewing…' : 'Run exposure brief'}
        </button>
      </div>

      {error && (
        <p className="mb-4 rounded-[12px] bg-[rgba(255,59,48,0.08)] px-3.5 py-2.5 text-sm text-[var(--bad)]">
          {error}
        </p>
      )}

      {!result && !loading && !error && (
        <div className="rounded-[16px] bg-[rgba(0,0,0,0.03)] px-4 py-10 text-center text-[14px] text-[var(--muted)]">
          File HIPAA policies, then run an OCR-minded exposure brief.
        </div>
      )}

      {result && (
        <div className="desk-rise space-y-4">
          <p className="text-[15px] leading-relaxed text-[var(--ink)]">{result.summary}</p>

          {result.findings.length > 0 && (
            <div className="space-y-2.5">
              {result.findings.map((finding) => (
                <article
                  key={`${finding.title}-${finding.severity}`}
                  className="rounded-[14px] bg-[rgba(0,0,0,0.03)] p-4"
                >
                  <div className="mb-1.5 flex items-center justify-between gap-2">
                    <h4 className="text-[15px] font-semibold tracking-[-0.015em] text-[var(--ink)]">
                      {finding.title}
                    </h4>
                    <span
                      className="text-[12px] font-semibold"
                      style={{ color: severityColor[finding.severity] || 'inherit' }}
                    >
                      {finding.severity}
                    </span>
                  </div>
                  <p className="text-[14px] leading-relaxed text-[var(--muted)]">{finding.detail}</p>
                  {finding.recommendation && (
                    <p className="mt-2 text-[14px] text-[var(--ink)]">
                      <span className="font-semibold text-[var(--accent)]">Action · </span>
                      {finding.recommendation}
                    </p>
                  )}
                </article>
              ))}
            </div>
          )}

          {result.strengths.length > 0 && (
            <div>
              <p className="desk-kicker mb-2.5">Residual strengths</p>
              <ul className="space-y-2">
                {result.strengths.map((item) => (
                  <li key={item} className="flex gap-2 text-[14px] text-[var(--ink-soft)]">
                    <span className="text-[var(--ok)]">•</span>
                    <span>{item}</span>
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
