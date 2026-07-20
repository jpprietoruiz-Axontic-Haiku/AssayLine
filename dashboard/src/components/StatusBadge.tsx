import type { ReportStatus } from '../api/types'

const LABELS: Record<ReportStatus, string> = {
  uploaded: 'Subido',
  processing: 'Procesando',
  transcribed: 'Transcrito',
  extracted: 'Extraído',
  reviewed: 'Revisado',
  failed: 'Error',
}

export function StatusBadge({ status }: { status: ReportStatus }) {
  return <span className={`badge badge-status-${status}`}>{LABELS[status] ?? status}</span>
}
