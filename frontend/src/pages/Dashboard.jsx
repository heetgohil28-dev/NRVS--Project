import { useState, useEffect } from 'react'
import api from '../services/api'
import ScoreCard from '../components/ScoreCard'
import SeverityBar from '../charts/SeverityBar'
import ScanTimeline from '../charts/ScanTimeline'
import { useNavigate } from 'react-router-dom'

export default function Dashboard() {
  const [summary,   setSummary]   = useState(null)
  const [severity,  setSeverity]  = useState([])
  const [trend,     setTrend]     = useState([])
  const [recent,    setRecent]    = useState([])
  const [loading,   setLoading]   = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([
      api.get('/dashboard/summary'),
      api.get('/dashboard/severity-breakdown'),
      api.get('/dashboard/vuln-trend'),
      api.get('/dashboard/recent-scans'),
    ]).then(([s, sv, t, r]) => {
      setSummary(s.data)
      setSeverity(sv.data)
      setTrend(t.data)
      setRecent(r.data)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-sky-500"/>
    </div>
  )

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Dashboard</h2>
        <button className="btn-primary" onClick={() => navigate('/scan/new')}>
          + New Scan
        </button>
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <ScoreCard title="Total Scans"   value={summary?.total_scans}     color="sky"/>
        <ScoreCard title="Total Hosts"   value={summary?.total_hosts}     color="green"/>
        <ScoreCard title="Total Assets"  value={summary?.total_assets}    color="sky"/>
        <ScoreCard title="Vulnerabilities" value={summary?.vulnerabilities?.total} color="red"/>
      </div>

      {/* Vuln breakdown */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <ScoreCard title="Critical" value={summary?.vulnerabilities?.critical} color="red"/>
        <ScoreCard title="High"     value={summary?.vulnerabilities?.high}     color="orange"/>
        <ScoreCard title="Medium"   value={summary?.vulnerabilities?.medium}   color="yellow"/>
        <ScoreCard title="Low"      value={summary?.vulnerabilities?.low}      color="sky"/>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Severity Breakdown</h3>
          <SeverityBar data={severity}/>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Vulnerability Trend (7 days)</h3>
          <ScanTimeline data={trend}/>
        </div>
      </div>

      {/* Recent Scans */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Recent Scans</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 text-xs uppercase border-b border-gray-800">
                <th className="text-left py-2 pr-4">ID</th>
                <th className="text-left py-2 pr-4">Targets</th>
                <th className="text-left py-2 pr-4">Profile</th>
                <th className="text-left py-2 pr-4">Status</th>
                <th className="text-left py-2">Hosts</th>
              </tr>
            </thead>
            <tbody>
              {recent.map(s => (
                <tr key={s.scan_id}
                  className="border-b border-gray-800 hover:bg-gray-800 cursor-pointer transition-colors"
                  onClick={() => navigate(`/scan/${s.scan_id}`)}>
                  <td className="py-2 pr-4 text-sky-400 font-mono">#{s.scan_id}</td>
                  <td className="py-2 pr-4 text-gray-300">{s.targets?.join(', ')}</td>
                  <td className="py-2 pr-4 text-gray-400">{s.profile}</td>
                  <td className="py-2 pr-4">
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                      s.status === 'completed' ? 'bg-green-900 text-green-300' :
                      s.status === 'running'   ? 'bg-sky-900 text-sky-300' :
                      s.status === 'failed'    ? 'bg-red-900 text-red-300' :
                                                 'bg-gray-800 text-gray-400'
                    }`}>{s.status}</span>
                  </td>
                  <td className="py-2 text-gray-300">{s.hosts_found}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
