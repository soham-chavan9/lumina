'use client'

import { Loader2, ShieldCheck } from 'lucide-react'
import type { RiskScanResponse } from '../lib/api'

type Props = {
  result: RiskScanResponse | null
  loading?: boolean
  error?: string | null
  onScan: () => void
  disabled?: boolean
}

const severityColor: Record<string, string> = {
  High: 'var(--lumina-red)',
  Medium: 'var(--lumina-orange)',
  Low: 'var(--lumina-green)',
}

export default function RiskScan({ result, loading, error, onScan, disabled }: Props) {
  return (
    <section className="lumina-panel p-5 md:p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[13px] font-semibold uppercase tracking-[0.08em] text-[var(--lumina-faint)]">
            MVP · Scan
          </p>
          <h2 className="mt-1 text-[22px] font-semibold tracking-tight">Compliance risk scan</h2>
          <p className="mt-1 max-w-xl text-sm text-[var(--lumina-muted)]">
            One-click brief of gaps, strengths, and recommended follow-ups from your indexed policies.
          </p>
        </div>
        <button
          type="button"
          className="lumina-btn lumina-btn-primary"
          onClick={onScan}
          disabled={disabled || loading}
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <ShieldCheck size={16} />}
          {loading ? 'Scanning…' : 'Run scan'}
        </button>
      </div>

      {error && (
        <p className="mb-3 rounded-[14px] bg-[rgba(255,59,48,0.08)] px-3 py-2 text-sm text-[var(--lumina-red)]">
          {error}
        </p>
      )}

      {!result && !loading && !error && (
        <div className="rounded-[18px] border border-dashed border-[var(--lumina-line)] px-4 py-8 text-center text-sm text-[var(--lumina-muted)]">
          Upload policies, then run a scan to generate your first risk brief.
        </div>
      )}

      {result && (
        <div className="lumina-enter space-y-4">
          <p className="text-[15px] leading-relaxed text-[var(--lumina-ink)]">{result.summary}</p>

          {result.findings.length > 0 && (
            <div className="space-y-2">
              {result.findings.map((finding) => (
                <article
                  key={`${finding.title}-${finding.severity}`}
                  className="rounded-[16px] bg-[rgba(0,0,0,0.03)] p-4"
                >
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <h4 className="text-sm font-semibold">{finding.title}</h4>
                    <span
                      className="text-xs font-semibold uppercase tracking-wide"
                      style={{ color: severityColor[finding.severity] || 'inherit' }}
                    >
                      {finding.severity}
                    </span>
                  </div>
                  <p className="text-sm text-[var(--lumina-muted)]">{finding.detail}</p>
                  {finding.recommendation && (
                    <p className="mt-2 text-sm text-[var(--lumina-ink)]">
                      <span className="font-semibold">Next: </span>
                      {finding.recommendation}
                    </p>
                  )}
                </article>
              ))}
            </div>
          )}

          {result.strengths.length > 0 && (
            <div>
              <p className="mb-2 text-sm font-semibold text-[var(--lumina-ink)]">Strengths</p>
              <ul className="space-y-1.5">
                {result.strengths.map((item) => (
                  <li key={item} className="text-sm text-[var(--lumina-muted)]">
                    · {item}
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
