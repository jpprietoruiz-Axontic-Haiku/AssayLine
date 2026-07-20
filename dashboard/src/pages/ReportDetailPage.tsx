import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, downloadExport, getReport, originalDocumentUrl, reviewReport } from '../api/client'
import { AnomalyCountBadge, SeverityBadge } from '../components/AnomalyBadge'
import { ConfidenceBar } from '../components/ConfidenceBar'
import { StatusBadge } from '../components/StatusBadge'
import type { FieldValue, ReportDetail, ReportStatus } from '../api/types'
import { TERMINAL_STATUSES } from '../api/types'

function coerceValue(raw: string): number | string | null {
  const trimmed = raw.trim()
  if (trimmed === '') return null
  const asNumber = Number(trimmed)
  return Number.isFinite(asNumber) ? asNumber : trimmed
}

function isPdf(filename: string): boolean {
  return filename.toLowerCase().endsWith('.pdf')
}

export function ReportDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [detail, setDetail] = useState<ReportDetail | null>(null)
  const [fieldInputs, setFieldInputs] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    if (!id) return
    try {
      const data = await getReport(id)
      setDetail(data)
      setError(null)
      setFieldInputs((prev) => {
        const next: Record<string, string> = { ...prev }
        for (const [field, payload] of Object.entries(data.extraction?.data ?? {})) {
          if (!(field in next)) next[field] = String(payload.value ?? '')
        }
        return next
      })
    } catch {
      setError('No se pudo cargar el informe.')
    }
  }, [id])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (!detail || TERMINAL_STATUSES.includes(detail.status as ReportStatus)) return
    const interval = setInterval(load, 2000)
    return () => clearInterval(interval)
  }, [detail, load])

  const anomaliesByField = useMemo(() => {
    const map = new Map<string, ReportDetail['anomalies'][number]>()
    detail?.anomalies.forEach((a) => map.set(a.field, a))
    return map
  }, [detail])

  async function handleSave(approve: boolean) {
    if (!id || !detail?.extraction) return
    const edits: Record<string, FieldValue> = {}
    for (const [field, raw] of Object.entries(fieldInputs)) {
      const original = detail.extraction.data[field]
      const coerced = coerceValue(raw)
      if (String(original?.value ?? '') !== raw) {
        edits[field] = { value: coerced, unit: original?.unit ?? null }
      }
    }

    setSaving(true)
    setError(null)
    try {
      const updated = await reviewReport(id, edits, approve)
      setDetail(updated)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo guardar la revisión.')
    } finally {
      setSaving(false)
    }
  }

  async function handleExport(format: 'json' | 'csv') {
    if (!id || !detail) return
    try {
      await downloadExport(id, format, detail.filename.replace(/\.[^.]+$/, ''))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo exportar el informe.')
    }
  }

  if (error && !detail) {
    return (
      <div className="page">
        <Link to="/">&larr; Volver</Link>
        <p className="error-text">{error}</p>
      </div>
    )
  }

  if (!detail) {
    return (
      <div className="page">
        <Link to="/">&larr; Volver</Link>
        <p>Cargando…</p>
      </div>
    )
  }

  const fields = Object.entries(detail.extraction?.data ?? {})

  return (
    <div className="page">
      <Link to="/">&larr; Volver a informes</Link>
      <header className="page-header">
        <div>
          <h1>{detail.filename}</h1>
          <p className="page-subtitle">
            {detail.report_type ?? 'Sin clasificar'} · <StatusBadge status={detail.status} />{' '}
            <AnomalyCountBadge
              count={detail.anomalies.length}
              hasCritical={detail.anomalies.some((a) => a.severity === 'critical')}
            />
          </p>
        </div>
        <div className="export-buttons">
          <button
            className="button"
            onClick={() => handleExport('csv')}
            disabled={!detail.extraction}
          >
            Exportar CSV
          </button>
          <button
            className="button"
            onClick={() => handleExport('json')}
            disabled={!detail.extraction}
          >
            Exportar JSON
          </button>
        </div>
      </header>

      {detail.status === 'failed' && (
        <p className="error-text">Error de procesamiento: {detail.error_message}</p>
      )}
      {error && <p className="error-text">{error}</p>}

      <div className="detail-grid">
        <div className="panel">
          <h2>Documento original</h2>
          {isPdf(detail.filename) ? (
            <iframe
              className="original-viewer"
              src={originalDocumentUrl(detail.id)}
              title="Documento original"
            />
          ) : (
            <img
              className="original-viewer"
              src={originalDocumentUrl(detail.id)}
              alt="Documento original"
            />
          )}
        </div>

        <div className="panel">
          <h2>Datos extraídos</h2>

          {!detail.extraction && <p>Todavía no hay datos extraídos para este informe.</p>}

          {detail.extraction && fields.length === 0 && (
            <p className="empty-state">El agente no extrajo campos de este informe.</p>
          )}

          {detail.extraction && fields.length > 0 && (
            <>
              <table className="table">
                <thead>
                  <tr>
                    <th>Campo</th>
                    <th>Valor</th>
                    <th>Unidad</th>
                    <th>Confianza</th>
                    <th>Anomalía</th>
                  </tr>
                </thead>
                <tbody>
                  {fields.map(([field, payload]) => {
                    const anomaly = anomaliesByField.get(field)
                    return (
                      <tr key={field} className={anomaly ? `row-${anomaly.severity}` : undefined}>
                        <td>{field}</td>
                        <td>
                          <input
                            className="field-input"
                            value={fieldInputs[field] ?? ''}
                            onChange={(e) =>
                              setFieldInputs((prev) => ({ ...prev, [field]: e.target.value }))
                            }
                          />
                        </td>
                        <td>{payload.unit ?? '—'}</td>
                        <td>
                          <ConfidenceBar value={detail.extraction?.confidence[field] as number} />
                        </td>
                        <td>
                          {anomaly ? (
                            <span title={`Esperado: ${anomaly.expected_range}`}>
                              <SeverityBadge severity={anomaly.severity} />
                            </span>
                          ) : (
                            '—'
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>

              {detail.extraction.validation_errors.length > 0 && (
                <div className="validation-errors">
                  <h3>Errores de validación</h3>
                  <ul>
                    {detail.extraction.validation_errors.map((err, i) => (
                      <li key={i}>{JSON.stringify(err)}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="review-actions">
                <button
                  className="button"
                  onClick={() => handleSave(false)}
                  disabled={saving || detail.status === 'reviewed'}
                >
                  {saving ? 'Guardando…' : 'Guardar cambios'}
                </button>
                <button
                  className="button button-primary"
                  onClick={() => handleSave(true)}
                  disabled={saving || detail.status === 'reviewed'}
                >
                  {saving ? 'Guardando…' : 'Aprobar y marcar revisado'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
