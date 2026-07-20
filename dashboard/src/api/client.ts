import type {
  FieldValue,
  ReportDetail,
  ReportListItem,
  ReportOut,
  SchemasResponse,
} from './types'

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    const text = await response.text().catch(() => '')
    throw new ApiError(response.status, text || response.statusText)
  }
  return (await response.json()) as T
}

export function listReports(status?: string): Promise<ReportListItem[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  return request(`/reports${query}`)
}

export function getReport(id: string): Promise<ReportDetail> {
  return request(`/reports/${id}`)
}

export function getSchemas(): Promise<SchemasResponse> {
  return request('/schemas')
}

export function originalDocumentUrl(id: string): string {
  return `${API_BASE_URL}/reports/${id}/original`
}

export function uploadReport(file: File): Promise<ReportOut> {
  const formData = new FormData()
  formData.append('file', file)
  return request('/reports', { method: 'POST', body: formData })
}

export function reviewReport(
  id: string,
  edits: Record<string, FieldValue>,
  approve: boolean,
): Promise<ReportDetail> {
  return request(`/reports/${id}/review`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ edits, approve }),
  })
}

export async function downloadExport(
  id: string,
  format: 'json' | 'csv',
  filenameHint: string,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/reports/${id}/export?format=${format}`, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new ApiError(response.status, await response.text().catch(() => response.statusText))
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${filenameHint}_export.${format}`
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}
