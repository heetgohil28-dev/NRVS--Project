export default function CVEBadge({ severity }) {
  const map = {
    critical:      'badge-critical',
    high:          'badge-high',
    medium:        'badge-medium',
    low:           'badge-low',
    informational: 'badge-info',
    none:          'badge-info',
  }
  const cls = map[severity?.toLowerCase()] || 'badge-info'
  return (
    <span className={cls}>
      {severity?.toUpperCase() || 'UNKNOWN'}
    </span>
  )
}
