import axios from 'axios'

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

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

export async function askQuestion(question: string) {
  const { data } = await axios.post<AskResponse>(`${API_BASE}/ask`, { question })
  return data
}

export async function uploadPdfs(files: FileList | File[]) {
  const form = new FormData()
  Array.from(files).forEach((file) => form.append('files', file))
  const { data } = await axios.post(`${API_BASE}/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data as {
    summary: string
    results: { filename: string; status: string; preview?: string; chunks?: number }[]
  }
}

export async function fetchDocuments() {
  const { data } = await axios.get<{ documents: DocumentInfo[]; total_chunks: number }>(
    `${API_BASE}/documents`
  )
  return data
}

export async function clearDocuments() {
  const { data } = await axios.delete<{ documents: DocumentInfo[]; total_chunks: number }>(
    `${API_BASE}/documents`
  )
  return data
}

export async function fetchSuggestions() {
  const { data } = await axios.get<{ suggestions: SuggestionItem[] }>(
    `${API_BASE}/suggestions`
  )
  return data.suggestions
}

export async function runRiskScan() {
  const { data } = await axios.post<RiskScanResponse>(`${API_BASE}/scan`)
  return data
}
