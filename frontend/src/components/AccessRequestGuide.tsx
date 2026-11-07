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
    <section className="desk-panel p-5 md:p-6">
      <p className="desk-kicker">Individual rights</p>
      <h2 className="mt-1 text-[1.45rem] text-[var(--ink)]">Patient access request guide</h2>
      <p className="mt-1 text-sm leading-relaxed text-[var(--muted)]">
        Access requests die in inboxes. Start the 30-day clock, pull the checklist from your
        filed policies, and surface denial/delay rules before OCR asks.
      </p>

      <form onSubmit={onSubmit} className="mt-4 grid gap-3 md:grid-cols-2">
        <label className="text-sm text-[var(--ink-soft)]">
          Request type
          <select
            value={requestType}
            onChange={(e) => setRequestType(e.target.value as typeof requestType)}
            disabled={disabled || loading}
            className="mt-1 w-full rounded-[14px] border border-[var(--line)] bg-white px-3 py-2.5"
          >
            <option value="access">Access (§164.524)</option>
            <option value="amendment">Amendment</option>
            <option value="restriction">Restriction</option>
            <option value="accounting">Accounting of disclosures</option>
          </select>
        </label>
        <label className="text-sm text-[var(--ink-soft)]">
          Received date
          <input
            type="date"
            required
            value={receivedAt}
            onChange={(e) => setReceivedAt(e.target.value)}
            disabled={disabled || loading}
            className="mt-1 w-full rounded-[14px] border border-[var(--line)] bg-white px-3 py-2.5"
          />
        </label>
        <label className="text-sm text-[var(--ink-soft)]">
          Channel
          <input
            value={channel}
            onChange={(e) => setChannel(e.target.value)}
            disabled={disabled || loading}
            className="mt-1 w-full rounded-[14px] border border-[var(--line)] bg-white px-3 py-2.5"
          />
        </label>
        <label className="text-sm text-[var(--ink-soft)]">
          Notes
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={disabled || loading}
            className="mt-1 w-full rounded-[14px] border border-[var(--line)] bg-white px-3 py-2.5"
            placeholder="Records requested, date range, format…"
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
        <p className="mt-3 rounded-[12px] bg-[rgba(159,18,57,0.08)] px-3 py-2 text-sm text-[var(--bad)]">
          {error}
        </p>
      )}

      {result && (
        <div className="desk-rise mt-5 space-y-4 border-t border-[var(--line)] pt-4">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="desk-kicker">Action deadline</p>
              <p className="mt-1 font-[family-name:var(--font-display)] text-2xl text-[var(--ink)]">
                {result.statutory_deadline}
              </p>
            </div>
            <div className="rounded-full border border-[var(--line)] bg-white px-3 py-1.5 text-sm tabular-nums">
              {result.days_remaining == null
                ? '—'
                : result.days_remaining >= 0
                  ? `${result.days_remaining} days remaining`
                  : `${Math.abs(result.days_remaining)} days overdue`}
            </div>
          </div>
          <p className="text-sm leading-relaxed text-[var(--ink)]">{result.summary}</p>
          <div>
            <p className="desk-kicker mb-2">Fulfillment checklist</p>
            <ul className="space-y-1.5 text-sm text-[var(--ink-soft)]">
              {result.checklist.map((item) => (
                <li key={item}>— {item}</li>
              ))}
            </ul>
          </div>
          {result.denial_or_delay_rules.length > 0 && (
            <div>
              <p className="desk-kicker mb-2">Denial / delay rules</p>
              <ul className="space-y-1.5 text-sm text-[var(--ink-soft)]">
                {result.denial_or_delay_rules.map((item) => (
                  <li key={item}>— {item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
