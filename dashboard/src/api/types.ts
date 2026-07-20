export type ReportStatus =
  | 'uploaded'
  | 'processing'
  | 'transcribed'
  | 'extracted'
  | 'reviewed'
  | 'failed'

export interface ReportOut {
  id: string
  filename: string
  report_type: string | null
  status: ReportStatus
  uploaded_at: string
  error_message: string | null
}

export interface ReportListItem extends ReportOut {
  anomaly_count: number
  has_critical_anomaly: boolean
}

export interface FieldValue {
  value: number | string | null
  unit: string | null
}

export interface ExtractionOut {
  id: string
  schema_version: string
  data: Record<string, FieldValue>
  confidence: Record<string, number>
  validation_errors: unknown[]
  created_at: string
}

export type AnomalySeverity = 'warning' | 'critical'

export interface AnomalyOut {
  id: string
  field: string
  value: string | null
  expected_range: string | null
  severity: AnomalySeverity
}

export interface ReportDetail extends ReportOut {
  extraction: ExtractionOut | null
  anomalies: AnomalyOut[]
}

export interface SchemaField {
  field: string
  min: number | null
  max: number | null
  unit: string | null
}

export type SchemasResponse = Record<string, SchemaField[]>

export const TERMINAL_STATUSES: ReportStatus[] = ['extracted', 'reviewed', 'failed']
