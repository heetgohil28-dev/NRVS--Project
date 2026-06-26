import CVEBadge from './CVEBadge'
import { Monitor, Globe, Shield } from 'lucide-react'

export default function HostCard({ host }) {
  const gradeColor = {
    'A+': 'text-green-400', 'A': 'text-green-400',
    'B':  'text-yellow-400',
    'C':  'text-orange-400',
    'D':  'text-red-400',   'F': 'text-red-500',
  }

  return (
    <div className="card hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Monitor size={16} className="text-sky-400"/>
          <span className="font-mono font-semibold text-white">{host.ip}</span>
          {host.hostname && (
            <span className="text-gray-500 text-sm">({host.hostname})</span>
          )}
        </div>
        <span className={`text-2xl font-bold ${gradeColor[host.grade] || 'text-gray-400'}`}>
          {host.grade || '—'}
        </span>
      </div>

      <div className="flex flex-wrap gap-3 text-sm text-gray-400 mb-3">
        {host.os && (
          <span className="flex items-center gap-1">
            <Globe size={13}/> {host.os}
          </span>
        )}
        <span className="flex items-center gap-1">
          <Shield size={13}/> {host.open_ports} open ports
        </span>
        <span className="text-sky-400 font-semibold">
          Risk: {host.risk_score?.toFixed(1)}
        </span>
      </div>

      {host.vulns > 0 && (
        <div className="text-xs text-gray-500">
          {host.vulns} vulnerabilities found
        </div>
      )}
    </div>
  )
}
