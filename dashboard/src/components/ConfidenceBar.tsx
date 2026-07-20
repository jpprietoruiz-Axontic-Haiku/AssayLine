export function ConfidenceBar({ value }: { value: number | undefined }) {
  const pct = Math.round((value ?? 0) * 100)
  const level = pct >= 80 ? 'high' : pct >= 50 ? 'medium' : 'low'
  return (
    <div className="confidence" title={`${pct}% de confianza`}>
      <div className={`confidence-fill confidence-${level}`} style={{ width: `${pct}%` }} />
      <span className="confidence-label">{pct}%</span>
    </div>
  )
}
