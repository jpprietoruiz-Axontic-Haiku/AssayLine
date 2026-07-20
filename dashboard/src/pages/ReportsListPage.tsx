import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listReports } from '../api/client'
import { AnomalyCountBadge } from '../components/AnomalyBadge'
import { StatusBadge } from '../components/StatusBadge'
import { UploadForm } from '../components/UploadForm'
import type { ReportListItem, ReportStatus } from '../api/types'
import { TERMINAL_STATUSES } from '../api/types'

const REPORT_TYPE_LABELS: Record<string, string> = {
  certificate_of_analysis: 'Certificado de análisis',
  process_log: 'Log de proceso',
  unknown: 'Sin clasificar',
}

export function ReportsListPage() {
  const [reports, setReports] = useState<ReportListItem[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const load = useCallback(async () => {
    try {
      const data = await listReports()
      setReports(data)
      setError(null)
    } catch {
      setError('No se pudo cargar la lista de informes. ¿Está el worker corriendo?')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    const hasPending = reports?.some((r) => !TERMINAL_STATUSES.includes(r.status as ReportStatus))
    if (!hasPending) return
    const interval = setInterval(load, 3000)
    return () => clearInterval(interval)
  }, [reports, load])

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Informes</h1>
          <p className="page-subtitle">
            Certificados de análisis y logs de proceso ingeridos por AssayLine.
          </p>
        </div>
        <UploadForm onUploaded={(id) => navigate(`/reports/${id}`)} />
      </header>

      {error && <p className="error-text">{error}</p>}

      {reports === null && !error && <p>Cargando…</p>}

      {reports !== null && reports.length === 0 && (
        <p className="empty-state">Todavía no hay informes. Sube el primero arriba.</p>
      )}

      {reports !== null && reports.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>Archivo</th>
              <th>Tipo</th>
              <th>Estado</th>
              <th>Anomalías</th>
              <th>Subido</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr
                key={report.id}
                className="table-row-clickable"
                onClick={() => navigate(`/reports/${report.id}`)}
              >
                <td>{report.filename}</td>
                <td>
                  {report.report_type
                    ? (REPORT_TYPE_LABELS[report.report_type] ?? report.report_type)
                    : '—'}
                </td>
                <td>
                  <StatusBadge status={report.status} />
                </td>
                <td>
                  <AnomalyCountBadge
                    count={report.anomaly_count}
                    hasCritical={report.has_critical_anomaly}
                  />
                </td>
                <td>{new Date(report.uploaded_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
