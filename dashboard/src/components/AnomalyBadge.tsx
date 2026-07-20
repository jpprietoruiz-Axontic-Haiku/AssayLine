import type { AnomalySeverity } from '../api/types'

export function AnomalyCountBadge({
  count,
  hasCritical,
}: {
  count: number
  hasCritical: boolean
}) {
  if (count === 0) {
    return <span className="badge badge-ok">Sin anomalías</span>
  }
  return (
    <span className={`badge ${hasCritical ? 'badge-critical' : 'badge-warning'}`}>
      {count} {count === 1 ? 'anomalía' : 'anomalías'}
    </span>
  )
}

export function SeverityBadge({ severity }: { severity: AnomalySeverity }) {
  const label = severity === 'critical' ? 'Crítico' : 'Advertencia'
  return <span className={`badge badge-${severity}`}>{label}</span>
}
