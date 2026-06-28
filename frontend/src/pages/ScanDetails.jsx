import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { scanService } from '../services/scanService'
import { reportService } from '../services/reportService'
import HostCard from '../components/HostCard'
import RiskDistribution from '../charts/RiskDistribution'
import PortFrequency from '../charts/PortFrequency'
import { RefreshCw } from 'lucide-react'

export default function ScanDetails() {
<<<<<<< HEAD
  const { id }                  = useParams()
  const navigate                = useNavigate()
  const [scan,    setScan]      = useState(null)
  const [results, setResults]   = useState(null)
  const [loading, setLoading]   = useState(true)
  const [reporting,setReporting]= useState(false)
  const [stopping, setStopping]  = useState(false)
=======
  const { id }                    = useParams()
  const navigate                  = useNavigate()
  const [scan,      setScan]      = useState(null)
  const [results,   setResults]   = useState(null)
  const [loading,   setLoading]   = useState(true)
  const [reporting, setReporting] = useState(false)
  const [activeTab, setActiveTab] = useState('hosts')
>>>>>>> heet-scan-engine

  const loadScan = useCallback(async () => {
    try {
      const s = await scanService.getScan(id)
      setScan(s)
      if (s.status === 'completed') {
        const r = await scanService.getScanResults(id)
        setResults(r)
      }
    } catch (err) {
      console.error('Load scan error:', err)
    } finally {
      setLoading(false)
    }
  }, [id])

<<<<<<< HEAD
  const stopScan = async () => {
    if (!confirm('Stop this scan?')) return
    setStopping(true)
    try {
      await scanService.stopScan(id)
      const updated = await scanService.getScan(id)
      setScan(updated)
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to stop scan')
    } finally {
      setStopping(false)
    }
  }
=======
  useEffect(() => { loadScan() }, [loadScan])

  // Poll every 5 seconds if scan is still running
  useEffect(() => {
    if (!scan) return
    if (scan.status === 'completed' || scan.status === 'failed') return
    const interval = setInterval(() => loadScan(), 5000)
    return () => clearInterval(interval)
  }, [scan, loadScan])
>>>>>>> heet-scan-engine

  const generateReport = async type => {
    setReporting(true)
    try {
      await reportService.generateReport(Number(id), type)
      alert(`${type.toUpperCase()} report queued successfully! Check Reports page.`)
    } catch (err) {
      alert(err.response?.data?.detail || 'Report generation failed')
    } finally {
      setReporting(false)
    }
  }

  const allPorts = results?.hosts?.flatMap(h => h.ports) || []

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-sky-500"/>
    </div>
  )

  if (!scan) return (
    <div className="text-center py-12">
      <p className="text-gray-500 mb-4">Scan not found</p>
      <button className="btn-ghost" onClick={() => navigate('/scan/history')}>
        ← Back to History
      </button>
    </div>
  )

  return (
    <div className="flex flex-col gap-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Scan #{id}</h2>
          <p className="text-gray-500 text-sm">
            {scan?.targets?.join(', ')} — {scan?.scan_profile || scan?.profile || '—'} profile
            {scan?.custom_args && (
              <span className="text-gray-600 ml-2 font-mono text-xs">{scan.custom_args}</span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={() => navigate('/history')}>
            ← Back
          </button>
<<<<<<< HEAD
          {scan?.status === 'running' || scan?.status === 'pending' ? (
            <button
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50"
              disabled={stopping}
              onClick={stopScan}>
              {stopping ? 'Stopping...' : 'Stop Scan'}
            </button>
          ) : null}
          <button
            className="btn-primary"
            disabled={reporting || scan?.status !== 'completed'}
            onClick={() => generateReport('pdf')}>
            {reporting ? 'Generating...' : 'Export PDF'}
          </button>
=======
          {scan?.status !== 'completed' && (
            <button
              className="btn-ghost flex items-center gap-2"
              onClick={loadScan}
            >
              <RefreshCw size={14}/> Refresh
            </button>
          )}
          {scan?.status === 'completed' && (
            <>
              <button
                className="btn-ghost"
                disabled={reporting}
                onClick={() => generateReport('json')}
              >
                Export JSON
              </button>
              <button
                className="btn-primary"
                disabled={reporting}
                onClick={() => generateReport('pdf')}
              >
                {reporting ? 'Generating...' : 'Export PDF'}
              </button>
            </>
          )}
>>>>>>> heet-scan-engine
        </div>
      </div>

      {/* Status Bar */}
      <div className="card flex flex-wrap gap-6 text-sm">
        <div>
          <span className="text-gray-500">Status </span>
          <span className={`font-semibold ${
            scan?.status === 'completed' ? 'text-green-400' :
            scan?.status === 'failed'    ? 'text-red-400'   :
            scan?.status === 'running'   ? 'text-sky-400'   : 'text-gray-400'
          }`}>
            {scan?.status}
            {scan?.status === 'running' && (
              <span className="ml-2 inline-block animate-spin">⟳</span>
            )}
          </span>
        </div>
        <div>
          <span className="text-gray-500">Progress </span>
          <span className="text-white font-semibold">{scan?.progress ?? 0}%</span>
        </div>
        <div>
          <span className="text-gray-500">Hosts Found </span>
          <span className="text-white font-semibold">{results?.total_hosts ?? 0}</span>
        </div>
        {scan?.started_at && (
          <div>
            <span className="text-gray-500">Started </span>
            <span className="text-gray-300 text-xs">
              {new Date(scan.started_at).toLocaleString()}
            </span>
          </div>
        )}
        {scan?.completed_at && (
          <div>
            <span className="text-gray-500">Completed </span>
            <span className="text-gray-300 text-xs">
              {new Date(scan.completed_at).toLocaleString()}
            </span>
          </div>
        )}
      </div>

      {/* Running State */}
      {scan?.status === 'running' && (
        <div className="card border-sky-800">
          <div className="flex items-center gap-3 mb-3">
            <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-sky-500"/>
            <span className="text-sky-400 text-sm font-semibold">Scan in progress...</span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-2">
            <div
              className="h-2 rounded-full bg-sky-500 transition-all duration-700"
              style={{ width: `${scan.progress ?? 0}%` }}
            />
          </div>
        </div>
      )}

      {/* Failed State */}
      {scan?.status === 'failed' && (
        <div className="card border-red-800 bg-red-950">
          <p className="text-red-400 text-sm font-semibold">
            ❌ Scan failed or was stopped
          </p>
          <p className="text-gray-500 text-xs mt-1">
            Check that nmap is installed and targets are reachable.
          </p>
        </div>
      )}

      {/* Results */}
      {results && (
        <>
          {/* Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-300 mb-4">Port Frequency</h3>
              {allPorts.length > 0
                ? <PortFrequency ports={allPorts}/>
                : <p className="text-gray-600 text-sm text-center py-8">No open ports found</p>
              }
            </div>
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-300 mb-4">Risk Distribution</h3>
              <RiskDistribution data={[
                { severity: 'critical', count: results.hosts.filter(h => h.grade === 'F').length },
                { severity: 'high',     count: results.hosts.filter(h => h.grade === 'D').length },
                { severity: 'medium',   count: results.hosts.filter(h => h.grade === 'C').length },
                { severity: 'low',      count: results.hosts.filter(h => ['A','A+','B'].includes(h.grade)).length },
              ].filter(d => d.count > 0)}/>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 border-b border-gray-800">
            {['hosts', 'ports'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm font-semibold capitalize transition-colors ${
                  activeTab === tab
                    ? 'text-sky-400 border-b-2 border-sky-400'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {tab === 'hosts'
                  ? `Hosts (${results.total_hosts})`
                  : `All Ports (${allPorts.length})`
                }
              </button>
            ))}
          </div>

          {/* Hosts Tab */}
          {activeTab === 'hosts' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.hosts.length > 0
                ? results.hosts.map((h, i) => <HostCard key={i} host={h}/>)
                : <p className="text-gray-500 col-span-2 text-center py-8">No hosts found</p>
              }
            </div>
          )}

          {/* Ports Tab */}
          {activeTab === 'ports' && (
            <div className="card overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 text-xs uppercase border-b border-gray-800">
                    <th className="text-left py-2 pr-4">Host</th>
                    <th className="text-left py-2 pr-4">Port</th>
                    <th className="text-left py-2 pr-4">Protocol</th>
                    <th className="text-left py-2 pr-4">State</th>
                    <th className="text-left py-2 pr-4">Service</th>
                    <th className="text-left py-2">Version</th>
                  </tr>
                </thead>
                <tbody>
                  {results.hosts.flatMap(h =>
                    h.ports.map((p, i) => (
                      <tr key={`${h.ip}-${p.port}-${i}`}
                        className="border-b border-gray-800 hover:bg-gray-800 transition-colors">
                        <td className="py-2 pr-4 font-mono text-sky-400 text-xs">{h.ip}</td>
                        <td className="py-2 pr-4 font-mono text-white">{p.port}</td>
                        <td className="py-2 pr-4 text-gray-400">{p.protocol}</td>
                        <td className="py-2 pr-4">
                          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                            p.state === 'open'     ? 'bg-green-900 text-green-300' :
                            p.state === 'filtered' ? 'bg-yellow-900 text-yellow-300' :
                                                     'bg-gray-800 text-gray-400'
                          }`}>{p.state}</span>
                        </td>
                        <td className="py-2 pr-4 text-gray-300">{p.service || '—'}</td>
                        <td className="py-2 text-gray-500 text-xs truncate max-w-xs">
                          {p.version || p.product || '—'}
                        </td>
                      </tr>
                    ))
                  )}
                  {allPorts.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-gray-500">
                        No ports found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}
