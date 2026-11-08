'use client'

import { FormEvent, useState } from 'react'
import { Loader2, FolderHeart } from 'lucide-react'
import {
  getErrorMessage,
  runAccessGuide,
  type AccessRequestGuideResponse,
} from '../lib/api'

type Props = { disabled?: boolean }

export default function AccessRequestGuide({ disabled }: Props) {
  const [requestType, setRequestType] = useState<
    'access' | 'amendment' | 'restriction' | 'accounting'
  >('access')
  const [receivedAt, setReceivedAt] = useState(new Date().toISOString().slice(0, 10))
  const [channel, setChannel] = useState('patient portal')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AccessRequestGuideResponse | null>(null)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (disabled || loading) return
    setLoading(true)
    setError(null)
    try {
      const data = await runAccessGuide({
        request_type: requestType,
        received_at: receivedAt,
        channel,
        notes,
      })
      setResult(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Access guide failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="desk-panel p-6 md:p-7">
      <p className="desk-kicker">Individual rights</p>
      <h2 className="section-title mt-1 text-[1.65rem]">Patient access request</h2>
      <p className="mt-2 text-[15px] leading-relaxed text-[var(--muted)]">
        Start the 30-day clock, pull the checklist, and surface denial or delay rules before OCR
        asks.
      </p>

      <form onSubmit={onSubmit} className="mt-5 grid gap-4 md:grid-cols-2">
        <label>
          <span className="label-quiet">Request type</span>
          <select
            value={requestType}
            onChange={(e) => setRequestType(e.target.value as typeof requestType)}
            disabled={disabled || loading}
            className="desk-field"
          >
            <option value="access">Access (§164.524)</option>
            <option value="amendment">Amendment</option>
            <option value="restriction">Restriction</option>
            <option value="accounting">Accounting of disclosures</option>
          </select>
        </label>
        <label>
          <span className="label-quiet">Received date</span>
          <input
            type="date"
            required
            value={receivedAt}
            onChange={(e) => setReceivedAt(e.target.value)}
            disabled={disabled || loading}
            className="desk-field"
          />
        </label>
        <label>
          <span className="label-quiet">Channel</span>
          <input
            value={channel}
            onChange={(e) => setChannel(e.target.value)}
            disabled={disabled || loading}
            className="desk-field"
          />
        </label>
        <label>
          <span className="label-quiet">Notes</span>
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={disabled || loading}
            className="desk-field"
            placeholder="Records, date range, format…"
          />
        </label>
        <div className="md:col-span-2">
          <button type="submit" className="desk-btn desk-btn-primary" disabled={disabled || loading}>
            {loading ? <Loader2 size={16} className="animate-spin" /> : <FolderHeart size={16} />}
            {loading ? 'Building guide…' : 'Open access guide'}
          </button>
        </div>
      </form>

      {error && (
        <p className="mt-4 rounded-[12px] bg-[rgba(255,59,48,0.08)] px-3.5 py-2.5 text-sm text-[var(--bad)]">
          {error}
        </p>
      )}

      {result && (
        <div className="desk-rise mt-6 space-y-5 border-t border-[var(--line)] pt-5">
          {result.mode === 'fallback' && (
            <p className="rounded-[12px] bg-[rgba(255,159,10,0.12)] px-3.5 py-2.5 text-[13px] text-[var(--ink-soft)]">
              Degraded mode — statutory shell only. Not grounded in filed policies. Confirm with
              Privacy/Legal before acting.
            </p>
          )}
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="desk-kicker">Action deadline</p>
              <p className="result-metric mt-1">{result.statutory_deadline}</p>
            </div>
            <span className="pill tabular-nums">
              {result.days_remaining == null
                ? '—'
                : result.days_remaining >= 0
                  ? `${result.days_remaining} days remaining`
                  : `${Math.abs(result.days_remaining)} days overdue`}
            </span>
          </div>
          <p className="text-[15px] leading-relaxed text-[var(--ink)]">{result.summary}</p>
          <div>
            <p className="desk-kicker mb-2.5">Fulfillment checklist</p>
            <ul className="space-y-2 text-[14px] text-[var(--ink-soft)]">
              {result.checklist.map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="text-[var(--accent)]">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
          {result.denial_or_delay_rules.length > 0 && (
            <div>
              <p className="desk-kicker mb-2.5">Denial / delay rules</p>
              <ul className="space-y-2 text-[14px] text-[var(--ink-soft)]">
                {result.denial_or_delay_rules.map((item) => (
                  <li key={item} className="flex gap-2">
                    <span className="text-[var(--accent)]">•</span>
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
