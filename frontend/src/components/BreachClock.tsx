'use client'

import { FormEvent, useState } from 'react'
import { Loader2, TimerReset } from 'lucide-react'
import {
  getErrorMessage,
  runBreachClock,
  type BreachClockResponse,
} from '../lib/api'

type Props = { disabled?: boolean }

export default function BreachClock({ disabled }: Props) {
  const [description, setDescription] = useState('')
  const [discoveredAt, setDiscoveredAt] = useState(
    new Date().toISOString().slice(0, 10)
  )
  const [recipient, setRecipient] = useState('')
  const [individuals, setIndividuals] = useState('')
  const [phiInvolved, setPhiInvolved] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<BreachClockResponse | null>(null)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (disabled || loading) return
    setLoading(true)
    setError(null)
    try {
      const data = await runBreachClock({
        description,
        discovered_at: discoveredAt,
        phi_involved: phiInvolved,
        unauthorized_recipient: recipient || undefined,
        individuals_affected: individuals ? Number(individuals) : null,
      })
      setResult(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Breach clock failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="desk-panel p-5 md:p-6">
      <p className="desk-kicker">Incident desk</p>
      <h2 className="mt-1 text-[1.45rem] text-[var(--ink)]">Breach notification clock</h2>
      <p className="mt-1 text-sm leading-relaxed text-[var(--muted)]">
        Privacy officers lose days when incidents sit in email. Capture discovery, run the
        four-factor screen against your filed policies, and lock the 60-day individual notice
        deadline.
      </p>

      <form onSubmit={onSubmit} className="mt-4 grid gap-3 md:grid-cols-2">
        <label className="md:col-span-2 text-sm text-[var(--ink-soft)]">
          What happened
          <textarea
            required
            minLength={10}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={disabled || loading}
            className="mt-1 w-full rounded-[14px] border border-[var(--line)] bg-white px-3 py-2.5 outline-none focus:border-[var(--teal)]"
            rows={3}
            placeholder="Wrong-patient email with discharge summary sent to external address…"
          />
        </label>
        <label className="text-sm text-[var(--ink-soft)]">
          Discovery date
          <input
            type="date"
            required
            value={discoveredAt}
            onChange={(e) => setDiscoveredAt(e.target.value)}
            disabled={disabled || loading}
            className="mt-1 w-full rounded-[14px] border border-[var(--line)] bg-white px-3 py-2.5"
          />
        </label>
        <label className="text-sm text-[var(--ink-soft)]">
          Individuals affected (est.)
          <input
            type="number"
            min={0}
            value={individuals}
            onChange={(e) => setIndividuals(e.target.value)}
            disabled={disabled || loading}
            className="mt-1 w-full rounded-[14px] border border-[var(--line)] bg-white px-3 py-2.5"
            placeholder="Optional"
          />
        </label>
        <label className="md:col-span-2 text-sm text-[var(--ink-soft)]">
          Unauthorized recipient
          <input
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            disabled={disabled || loading}
            className="mt-1 w-full rounded-[14px] border border-[var(--line)] bg-white px-3 py-2.5"
            placeholder="External clinic inbox, lost laptop, unknown actor…"
          />
        </label>
        <label className="flex items-center gap-2 text-sm text-[var(--ink)] md:col-span-2">
          <input
            type="checkbox"
            checked={phiInvolved}
            onChange={(e) => setPhiInvolved(e.target.checked)}
            disabled={disabled || loading}
          />
          Unsecured PHI appears involved
        </label>
        <div className="md:col-span-2">
          <button type="submit" className="desk-btn desk-btn-primary" disabled={disabled || loading}>
            {loading ? <Loader2 size={16} className="animate-spin" /> : <TimerReset size={16} />}
            {loading ? 'Assessing…' : 'Start breach clock'}
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
              <p className="desk-kicker">Individual notice deadline</p>
              <p className="mt-1 font-[family-name:var(--font-display)] text-2xl text-[var(--ink)]">
                {result.notification_deadline}
              </p>
            </div>
            <div className="rounded-full border border-[var(--line)] bg-white px-3 py-1.5 text-sm tabular-nums text-[var(--ink-soft)]">
              {result.days_remaining == null
                ? '—'
                : result.days_remaining >= 0
                  ? `${result.days_remaining} days remaining`
                  : `${Math.abs(result.days_remaining)} days overdue`}
            </div>
          </div>
          <p className="text-sm leading-relaxed text-[var(--ink)]">{result.summary}</p>
          <p className="text-sm font-semibold text-[var(--ink)]">
            Likely reportable: {result.likely_reportable ? 'Yes — escalate' : 'Unclear / document why not'}
          </p>
          <div className="grid gap-2 md:grid-cols-2">
            {result.four_factor.map((f) => (
              <article key={f.factor} className="rounded-[14px] border border-[var(--line)] bg-white p-3">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-sm font-semibold text-[var(--ink)]">{f.factor}</h4>
                  <span className="text-[11px] font-semibold uppercase tracking-wide text-[var(--teal)]">
                    {f.risk}
                  </span>
                </div>
                <p className="mt-1 text-sm text-[var(--muted)]">{f.assessment}</p>
              </article>
            ))}
          </div>
          {result.immediate_actions.length > 0 && (
            <ul className="space-y-1.5 text-sm text-[var(--ink-soft)]">
              {result.immediate_actions.map((a) => (
                <li key={a}>— {a}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  )
}
