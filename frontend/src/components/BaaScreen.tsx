'use client'

import { FormEvent, useState } from 'react'
import { Loader2, Handshake } from 'lucide-react'
import { getErrorMessage, runBaaScreen, type BaaScreenResponse } from '../lib/api'

type Props = { disabled?: boolean }

export default function BaaScreen({ disabled }: Props) {
  const [vendorName, setVendorName] = useState('')
  const [services, setServices] = useState('')
  const [phi, setPhi] = useState(true)
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<BaaScreenResponse | null>(null)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (disabled || loading) return
    setLoading(true)
    setError(null)
    try {
      const data = await runBaaScreen({
        vendor_name: vendorName,
        services,
        creates_receives_maintains_or_transmits_phi: phi,
        notes,
      })
      setResult(data)
    } catch (err) {
      setError(getErrorMessage(err, 'BAA screen failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="desk-panel p-5 md:p-6">
      <p className="desk-kicker">Vendor diligence</p>
      <h2 className="mt-1 text-[1.45rem] text-[var(--ink)]">BAA / vendor screen</h2>
      <p className="mt-1 text-sm leading-relaxed text-[var(--muted)]">
        Procurement moves faster than Privacy. Screen whether a Business Associate Agreement is
        required, which clauses your policies demand, and what to ask before PHI flows.
      </p>

      <form onSubmit={onSubmit} className="mt-4 grid gap-3 md:grid-cols-2">
        <label className="text-sm text-[var(--ink-soft)]">
          Vendor
          <input
            required
            value={vendorName}
            onChange={(e) => setVendorName(e.target.value)}
            disabled={disabled || loading}
            className="mt-1 w-full rounded-[14px] border border-[var(--line)] bg-white px-3 py-2.5"
            placeholder="Acme Cloud Transcription"
          />
        </label>
        <label className="flex items-center gap-2 self-end text-sm text-[var(--ink)]">
          <input
            type="checkbox"
            checked={phi}
            onChange={(e) => setPhi(e.target.checked)}
            disabled={disabled || loading}
          />
          Creates / receives / maintains / transmits PHI
        </label>
        <label className="md:col-span-2 text-sm text-[var(--ink-soft)]">
          Services
          <textarea
            required
            minLength={5}
            value={services}
            onChange={(e) => setServices(e.target.value)}
            disabled={disabled || loading}
            rows={3}
            className="mt-1 w-full rounded-[14px] border border-[var(--line)] bg-white px-3 py-2.5"
            placeholder="Hosts imaging archive; support staff can view studies remotely…"
          />
        </label>
        <label className="md:col-span-2 text-sm text-[var(--ink-soft)]">
          Notes
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={disabled || loading}
            className="mt-1 w-full rounded-[14px] border border-[var(--line)] bg-white px-3 py-2.5"
            placeholder="Subprocessors, offshore support, SOC 2 available…"
          />
        </label>
        <div className="md:col-span-2">
          <button type="submit" className="desk-btn desk-btn-primary" disabled={disabled || loading}>
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Handshake size={16} />}
            {loading ? 'Screening…' : 'Run BAA screen'}
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
          <div className="flex flex-wrap gap-2 text-sm">
            <span className="rounded-full border border-[var(--line)] bg-white px-3 py-1">
              BAA likely required: {result.ba_likely_required ? 'Yes' : 'No / confirm'}
            </span>
            <span className="rounded-full border border-[var(--line)] bg-white px-3 py-1">
              Risk: {result.risk_level}
            </span>
          </div>
          <p className="text-sm leading-relaxed text-[var(--ink)]">{result.summary}</p>
          {result.blockers.length > 0 && (
            <div>
              <p className="desk-kicker mb-2">Blockers before PHI</p>
              <ul className="space-y-1.5 text-sm text-[var(--bad)]">
                {result.blockers.map((b) => (
                  <li key={b}>— {b}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="desk-kicker mb-2">Clause pack</p>
              <ul className="space-y-1.5 text-sm text-[var(--ink-soft)]">
                {result.required_clauses.map((c) => (
                  <li key={c}>— {c}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="desk-kicker mb-2">Ask the vendor</p>
              <ul className="space-y-1.5 text-sm text-[var(--ink-soft)]">
                {result.diligence_questions.map((q) => (
                  <li key={q}>— {q}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
