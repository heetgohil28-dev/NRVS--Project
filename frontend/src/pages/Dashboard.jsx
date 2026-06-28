import { useState, useEffect, useCallback } from 'react'
import api from '../services/api'
import ScoreCard from '../components/ScoreCard'
import SeverityBar from '../charts/SeverityBar'
import ScanTimeline from '../charts/ScanTimeline'
import { useNavigate } from 'react-router-dom'
import { RefreshCw } from 'lucide-react'

export default function Dashboard() {
  const [summary,   setSummary]   = useState(null)
  const [severity,  setSeverity]  = useState([])
  const [trend,     setTrend]     = useState([])
  const [recent,    setRecent]    = useState([])
  const [risky,     setRisky]     = useState([])
  const [loading,   setLoading]   = useState(true)
  const [refreshing,setRefreshing]= useState(false)
  const [lastUpdate,setLastUpdate]= useState(null)
  const navigate = useNavigate()

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    try {
      const [s, sv, t, r, rh] = await Promise.all([
        api.get('/dashboard/summary'),
        api.get('/dashboard/severity-breakdown'),
        api.get('/dashboard/vuln-trend'),
        api.get('/dashboard/recent-scans'),
        api.get('/dashboard/top-risky-hosts'),
      ])
      setSummary(s.data)
      setSeverity(sv.data)
      setTrend(t.data)
      setRecent(r.data)
      setRisky(rh.data)
      setLastUpdate(new Date().toLocaleTimeString())
    } catch (err) {
      console.error('Dashboard load error:', err)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  // Initial load
  useEffect(() => { load() }, [load])

  // Auto refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => load(true), 30000)
    return () => clearInterval(interval)
  }, [load])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-sky-500"/>
    </div>
  )

  const hasData = summary?.total_scans > 0

  return (
    <div className="flex flex-col gap-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Dashboard</h2>
          {lastUpdate && (
            <p className="text-gray-600 text-xs mt-0.5">
              Last updated: {lastUpdate}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            className="btn-ghost flex items-center gap-2 text-sm"
            onClick={() => load(true)}
            disabled={refreshing}
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''}/>
            Refresh
          </button>
          <button className="btn-primary" onClick={() => navigate('/scan/new')}>
            + New Scan
          </button>
        </div>
      </div>

      {/* Score Cards — Row 1 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <ScoreCard
          title="Total Scans"
          value={summary?.total_scans ?? 0}
          sub={`${summary?.completed_scans ?? 0} completed`}
          color="sky"
        />
        <ScoreCard
          title="Total Hosts"
          value={summary?.total_hosts ?? 0}
          color="green"
        />
        <ScoreCard
          title="Total Assets"
          value={summary?.total_assets ?? 0}
          color="sky"
        />
        <ScoreCard
          title="Total Vulns"
          value={summary?.vulnerabilities?.total ?? 0}
          color="red"
        />
      </div>

      {/* Score Cards — Row 2 Vuln Breakdown */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <ScoreCard title="Critical" value={summary?.vulnerabilities?.critical ?? 0} color="red"/>
        <ScoreCard title="High"     value={summary?.vulnerabilities?.high     ?? 0} color="orange"/>
        <ScoreCard title="Medium"   value={summary?.vulnerabilities?.medium   ?? 0} color="yellow"/>
        <ScoreCard title="Low"      value={summary?.vulnerabilities?.low      ?? 0} color="sky"/>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">
            Severity Breakdown
          </h3>
          {severity.every(s => s.count === 0)
            ? <p className="text-gray-600 text-sm text-center py-8">No vulnerability data yet</p>
            : <SeverityBar data={severity}/>
          }
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">
            Vulnerability Trend (7 days)
          </h3>
          {trend.every(t => t.count === 0)
            ? <p className="text-gray-600 text-sm text-center py-8">No trend data yet</p>
            : <ScanTimeline data={trend}/>
          }
        </div>
      </div>

      {/* Top Risky Hosts */}
      {risky.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">
            Top Risky Hosts
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs uppercase border-b border-gray-800">
                  <th className="text-left py-2 pr-4">IP</th>
                  <th className="text-left py-2 pr-4">Hostname</th>
                  <th className="text-left py-2 pr-4">OS</th>
                  <th className="text-left py-2 pr-4">Risk Score</th>
                  <th className="text-left py-2 pr-4">Grade</th>
                  <th className="text-left py-2">Vulns</th>
                </tr>
              </thead>
              <tbody>
                {risky.map((h, i) => (
                  <tr key={i} className="border-b border-gray-800 hover:bg-gray-800 transition-colors">
                    <td className="py-2 pr-4 font-mono text-sky-400">{h.ip}</td>
                    <td className="py-2 pr-4 text-gray-300">{h.hostname || '—'}</td>
                    <td className="py-2 pr-4 text-gray-400">{h.os || '—'}</td>
                    <td className="py-2 pr-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-800 rounded-full h-1.5">
                          <div
                            className={`h-1.5 rounded-full ${
                              h.risk_score >= 60 ? 'bg-red-500' :
                              h.risk_score >= 30 ? 'bg-yellow-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${Math.min(h.risk_score, 100)}%` }}
                          />
                        </div>
                        <span className="text-gray-300 text-xs">{h.risk_score?.toFixed(1)}</span>
                      </div>
                    </td>
                    <td className="py-2 pr-4">
                      <span className={`font-bold text-sm ${
                        h.grade === 'F'           ? 'text-red-400'    :
                        h.grade === 'D'           ? 'text-orange-400' :
                        h.grade === 'C'           ? 'text-yellow-400' :
                        ['A','A+'].includes(h.grade) ? 'text-green-400' : 'text-gray-400'
                      }`}>{h.grade || '—'}</span>
                    </td>
                    <td className="py-2 text-gray-300">{h.vulns ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recent Scans */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Recent Scans</h3>
        {!hasData ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">No scans yet — run your first scan!</p>
            <button className="btn-primary" onClick={() => navigate('/scan/new')}>
              + Start First Scan
            </button>
          </div>
        ) : (
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
                  <tr
                    key={s.scan_id}
                    className="border-b border-gray-800 hover:bg-gray-800 cursor-pointer transition-colors"
                    onClick={() => navigate(`/scan/${s.scan_id}`)}
                  >
                    <td className="py-2 pr-4 text-sky-400 font-mono">#{s.scan_id}</td>
                    <td className="py-2 pr-4 text-gray-300 max-w-xs truncate">
                      {s.targets?.join(', ')}
                    </td>
                    <td className="py-2 pr-4 text-gray-400">
                      {s.scan_profile || s.profile || '—'}
                    </td>
                    <td className="py-2 pr-4">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                        s.status === 'completed' ? 'bg-green-900 text-green-300' :
                        s.status === 'running'   ? 'bg-sky-900 text-sky-300 animate-pulse' :
                        s.status === 'failed'    ? 'bg-red-900 text-red-300' :
                                                   'bg-gray-800 text-gray-400'
                      }`}>
                        {s.status}
                      </span>
                    </td>
                    <td className="py-2 text-gray-300">{s.hosts_found ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  )
}
