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
    <section className="desk-panel p-6 md:p-7">
      <p className="desk-kicker">Incident</p>
      <h2 className="section-title mt-1 text-[1.65rem]">Breach notification clock</h2>
      <p className="mt-2 text-[15px] leading-relaxed text-[var(--muted)]">
        Capture discovery, run the four-factor screen, and lock the 60-day individual notice
        deadline before the clock slips.
      </p>

      <form onSubmit={onSubmit} className="mt-5 grid gap-4 md:grid-cols-2">
        <label className="md:col-span-2">
          <span className="label-quiet">What happened</span>
          <textarea
            required
            minLength={10}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={disabled || loading}
            className="desk-field"
            rows={3}
            placeholder="Wrong-patient email with discharge summary sent externally…"
          />
        </label>
        <label>
          <span className="label-quiet">Discovery date</span>
          <input
            type="date"
            required
            value={discoveredAt}
            onChange={(e) => setDiscoveredAt(e.target.value)}
            disabled={disabled || loading}
            className="desk-field"
          />
        </label>
        <label>
          <span className="label-quiet">Individuals affected (est.)</span>
          <input
            type="number"
            min={0}
            value={individuals}
            onChange={(e) => setIndividuals(e.target.value)}
            disabled={disabled || loading}
            className="desk-field"
            placeholder="Optional"
          />
        </label>
        <label className="md:col-span-2">
          <span className="label-quiet">Unauthorized recipient</span>
          <input
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            disabled={disabled || loading}
            className="desk-field"
            placeholder="External inbox, lost laptop, unknown actor…"
          />
        </label>
        <label className="flex items-center gap-2.5 text-[14px] text-[var(--ink)] md:col-span-2">
          <input
            type="checkbox"
            checked={phiInvolved}
            onChange={(e) => setPhiInvolved(e.target.checked)}
            disabled={disabled || loading}
            className="h-4 w-4 accent-[var(--accent)]"
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
        <p className="mt-4 rounded-[12px] bg-[rgba(255,59,48,0.08)] px-3.5 py-2.5 text-sm text-[var(--bad)]">
          {error}
        </p>
      )}

      {result && (
        <div className="desk-rise mt-6 space-y-5 border-t border-[var(--line)] pt-5">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="desk-kicker">Individual notice deadline</p>
              <p className="result-metric mt-1">{result.notification_deadline}</p>
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
          <p className="text-[14px] font-semibold text-[var(--ink)]">
            Likely reportable:{' '}
            {result.likely_reportable ? 'Yes — escalate' : 'Unclear / document why not'}
          </p>
          <div className="grid gap-2.5 md:grid-cols-2">
            {result.four_factor.map((f) => (
              <article
                key={f.factor}
                className="rounded-[14px] bg-[rgba(0,0,0,0.03)] p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-[14px] font-semibold tracking-[-0.01em] text-[var(--ink)]">
                    {f.factor}
                  </h4>
                  <span className="text-[12px] font-medium text-[var(--accent)]">{f.risk}</span>
                </div>
                <p className="mt-1.5 text-[13px] leading-relaxed text-[var(--muted)]">
                  {f.assessment}
                </p>
              </article>
            ))}
          </div>
          {result.immediate_actions.length > 0 && (
            <ul className="space-y-2 text-[14px] text-[var(--ink-soft)]">
              {result.immediate_actions.map((a) => (
                <li key={a} className="flex gap-2">
                  <span className="text-[var(--accent)]">•</span>
                  <span>{a}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  )
}
