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
    <section className="desk-panel p-6 md:p-7">
      <p className="desk-kicker">Vendor diligence</p>
      <h2 className="section-title mt-1 text-[1.65rem]">BAA / vendor screen</h2>
      <p className="mt-2 text-[15px] leading-relaxed text-[var(--muted)]">
        Screen whether a Business Associate Agreement is required and which clauses to demand
        before PHI flows.
      </p>

      <form onSubmit={onSubmit} className="mt-5 grid gap-4 md:grid-cols-2">
        <label>
          <span className="label-quiet">Vendor</span>
          <input
            required
            value={vendorName}
            onChange={(e) => setVendorName(e.target.value)}
            disabled={disabled || loading}
            className="desk-field"
            placeholder="Acme Cloud Transcription"
          />
        </label>
        <label className="flex items-center gap-2.5 self-end pb-3 text-[14px] text-[var(--ink)]">
          <input
            type="checkbox"
            checked={phi}
            onChange={(e) => setPhi(e.target.checked)}
            disabled={disabled || loading}
            className="h-4 w-4 accent-[var(--accent)]"
          />
          Creates / receives / maintains / transmits PHI
        </label>
        <label className="md:col-span-2">
          <span className="label-quiet">Services</span>
          <textarea
            required
            minLength={5}
            value={services}
            onChange={(e) => setServices(e.target.value)}
            disabled={disabled || loading}
            rows={3}
            className="desk-field"
            placeholder="Hosts imaging archive; support staff can view studies remotely…"
          />
        </label>
        <label className="md:col-span-2">
          <span className="label-quiet">Notes</span>
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={disabled || loading}
            className="desk-field"
            placeholder="Subprocessors, offshore support, SOC 2…"
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
        <p className="mt-4 rounded-[12px] bg-[rgba(255,59,48,0.08)] px-3.5 py-2.5 text-sm text-[var(--bad)]">
          {error}
        </p>
      )}

      {result && (
        <div className="desk-rise mt-6 space-y-5 border-t border-[var(--line)] pt-5">
          <div className="flex flex-wrap gap-2">
            <span className="pill">
              BAA likely required: {result.ba_likely_required ? 'Yes' : 'No / confirm'}
            </span>
            <span className="pill">Risk: {result.risk_level}</span>
          </div>
          <p className="text-[15px] leading-relaxed text-[var(--ink)]">{result.summary}</p>
          {result.blockers.length > 0 && (
            <div>
              <p className="desk-kicker mb-2.5">Blockers before PHI</p>
              <ul className="space-y-2 text-[14px] text-[var(--bad)]">
                {result.blockers.map((b) => (
                  <li key={b} className="flex gap-2">
                    <span>•</span>
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <p className="desk-kicker mb-2.5">Clause pack</p>
              <ul className="space-y-2 text-[14px] text-[var(--ink-soft)]">
                {result.required_clauses.map((c) => (
                  <li key={c} className="flex gap-2">
                    <span className="text-[var(--accent)]">•</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="desk-kicker mb-2.5">Ask the vendor</p>
              <ul className="space-y-2 text-[14px] text-[var(--ink-soft)]">
                {result.diligence_questions.map((q) => (
                  <li key={q} className="flex gap-2">
                    <span className="text-[var(--accent)]">•</span>
                    <span>{q}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
