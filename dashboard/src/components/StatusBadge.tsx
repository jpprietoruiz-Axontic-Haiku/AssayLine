import type { ReportStatus } from '../api/types'

const LABELS: Record<ReportStatus, string> = {
  uploaded: 'Uploaded',
  processing: 'Processing',
  transcribed: 'Transcribed',
  extracted: 'Extracted',
  reviewed: 'Reviewed',
  failed: 'Failed',
}

export function StatusBadge({ status }: { status: ReportStatus }) {
  return <span className={`badge badge-status-${status}`}>{LABELS[status] ?? status}</span>
}
