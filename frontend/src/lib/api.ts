import axios, { AxiosError } from 'axios'

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 90_000,
  headers: { Accept: 'application/json' },
})

const browserApiKey = process.env.NEXT_PUBLIC_LUMINA_API_KEY
if (browserApiKey) {
  api.defaults.headers.common['X-API-Key'] = browserApiKey
}

const browserApiKey = process.env.NEXT_PUBLIC_LUMINA_API_KEY
if (browserApiKey) {
  api.defaults.headers.common['X-API-Key'] = browserApiKey
}

export function getErrorMessage(err: unknown, fallback = 'Something went wrong') {
  const ax = err as AxiosError<{ detail?: string | { msg?: string }[] }>
  const detail = ax.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (ax.code === 'ECONNABORTED') return 'Request timed out. Try again.'
  if (ax.message === 'Network Error') return 'Cannot reach Lumina API. Is the backend running?'
  return ax.message || fallback
}

export type AskResponse = {
  answer: string
  citation?: string
  confidence?: string
  sources?: string[]
  source_documents?: { source: string; snippet?: string }[]
  refused?: boolean
}

export type DocumentInfo = { source: string; chunks: number }

export type SuggestionItem = { question: string; category: string }

export type RiskFinding = {
  title: string
  severity: 'High' | 'Medium' | 'Low'
  detail: string
  recommendation?: string
}

export type RiskScanResponse = {
  summary: string
  findings: RiskFinding[]
  strengths: string[]
  sources: string[]
}

export type HealthResponse = {
  status: string
  message: string
  vector_store_ready: boolean
  document_chunks: number
  model: string
}

export async function fetchHealth() {
  const root = API_BASE.replace(/\/api\/?$/, '')
  const { data } = await axios.get<HealthResponse>(`${root}/health`, { timeout: 8_000 })
  return data
}

export async function askQuestion(question: string) {
  const { data } = await api.post<AskResponse>('/ask', { question })
  return data
}

export async function uploadPdfs(files: FileList | File[]) {
  const form = new FormData()
  Array.from(files).forEach((file) => form.append('files', file))
  const { data } = await api.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data as {
    summary: string
    results: { filename: string; status: string; preview?: string; chunks?: number }[]
  }
}

export async function fetchDocuments() {
  const { data } = await api.get<{ documents: DocumentInfo[]; total_chunks: number }>(
    '/documents'
  )
  return data
}

export async function clearDocuments() {
  const { data } = await api.delete<{ documents: DocumentInfo[]; total_chunks: number }>(
    '/documents'
  )
  return data
}

export async function fetchSuggestions() {
  const { data } = await api.get<{ suggestions: SuggestionItem[] }>('/suggestions')
  return data.suggestions
}

export async function runRiskScan() {
  const { data } = await api.post<RiskScanResponse>('/scan')
  return data
}

export type WorkflowMode = 'policy_grounded' | 'fallback'

export type BreachClockResponse = {
  summary: string
  notification_deadline: string
  days_remaining: number | null
  likely_reportable: boolean
  four_factor: { factor: string; assessment: string; risk: string }[]
  immediate_actions: string[]
  policy_citations: string[]
  sources: string[]
  mode?: WorkflowMode
}

export type AccessRequestGuideResponse = {
  summary: string
  statutory_deadline: string
  days_remaining: number | null
  checklist: string[]
  denial_or_delay_rules: string[]
  policy_citations: string[]
  sources: string[]
  mode?: WorkflowMode
}

export type BaaScreenResponse = {
  summary: string
  ba_likely_required: boolean
  risk_level: string
  required_clauses: string[]
  diligence_questions: string[]
  blockers: string[]
  policy_citations: string[]
  sources: string[]
  mode?: WorkflowMode
}

export async function runBreachClock(payload: {
  description: string
  discovered_at: string
  phi_involved: boolean
  individuals_affected?: number | null
  unauthorized_recipient?: string
}) {
  const { data } = await api.post<BreachClockResponse>('/breach-clock', payload)
  return data
}

export async function runAccessGuide(payload: {
  request_type: 'access' | 'amendment' | 'restriction' | 'accounting'
  received_at: string
  channel: string
  notes?: string
}) {
  const { data } = await api.post<AccessRequestGuideResponse>('/access-request', payload)
  return data
}

export async function runBaaScreen(payload: {
  vendor_name: string
  services: string
  creates_receives_maintains_or_transmits_phi: boolean
  notes?: string
}) {
  const { data } = await api.post<BaaScreenResponse>('/baa-screen', payload)
  return data
}
