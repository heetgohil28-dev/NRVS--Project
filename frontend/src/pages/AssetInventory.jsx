import { useState, useEffect } from 'react'
import api from '../services/api'
import { Search } from 'lucide-react'

export default function AssetInventory() {
  const [assets,  setAssets]  = useState([])
  const [summary, setSummary] = useState(null)
  const [search,  setSearch]  = useState('')
  const [loading, setLoading] = useState(true)

  const load = (q = '') => {
    api.get(`/assets/?search=${q}`)
      .then(r => setAssets(r.data.assets || []))
      .finally(() => setLoading(false))
    api.get('/assets/stats/summary').then(r => setSummary(r.data))
  }

  useEffect(() => { load() }, [])

  const handleSearch = e => {
    e.preventDefault()
    load(search)
  }

  const critColor = {
    critical: 'badge-critical',
    high:     'badge-high',
    medium:   'badge-medium',
    low:      'badge-low',
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-sky-500"/>
    </div>
  )

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-bold text-white">Asset Inventory</h2>

      {/* Summary */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Assets',    value: summary.total_assets    },
            { label: 'Critical Assets', value: summary.critical_assets },
            { label: 'High Risk',       value: summary.high_risk       },
            { label: 'By Criticality',  value: `${summary.by_criticality?.high || 0} High` },
          ].map((s, i) => (
            <div key={i} className="card">
              <span className="text-gray-500 text-xs uppercase">{s.label}</span>
              <span className="text-2xl font-bold text-sky-400">{s.value}</span>
            </div>
          ))}
        </div>
      )}

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"/>
          <input
            className="input pl-9"
            placeholder="Search by IP or hostname..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <button className="btn-primary">Search</button>
      </form>

      {/* Table */}
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-xs uppercase border-b border-gray-800">
              <th className="text-left py-2 pr-4">IP Address</th>
              <th className="text-left py-2 pr-4">Hostname</th>
              <th className="text-left py-2 pr-4">OS</th>
              <th className="text-left py-2 pr-4">Criticality</th>
              <th className="text-left py-2 pr-4">Risk Score</th>
              <th className="text-left py-2">Last Seen</th>
            </tr>
          </thead>
          <tbody>
            {assets.map(a => (
              <tr key={a.id} className="border-b border-gray-800 hover:bg-gray-800 transition-colors">
                <td className="py-2 pr-4 font-mono text-sky-400">{a.ip_address}</td>
                <td className="py-2 pr-4 text-gray-300">{a.hostname || '—'}</td>
                <td className="py-2 pr-4 text-gray-400">{a.os_name || '—'}</td>
                <td className="py-2 pr-4">
                  <span className={critColor[a.criticality] || 'badge-info'}>
                    {a.criticality}
                  </span>
                </td>
                <td className="py-2 pr-4 text-gray-300">{a.last_risk_score?.toFixed(1)}</td>
                <td className="py-2 text-gray-500 text-xs">
                  {a.last_seen ? new Date(a.last_seen).toLocaleDateString() : '—'}
                </td>
              </tr>
            ))}
            {!assets.length && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-gray-500">
                  No assets found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
