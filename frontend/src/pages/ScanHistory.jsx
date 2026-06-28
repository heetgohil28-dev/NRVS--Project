import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { scanService } from '../services/scanService'
import { Trash2, RefreshCw } from 'lucide-react'

export default function ScanHistory() {
  const [scans,     setScans]     = useState([])
  const [loading,   setLoading]   = useState(true)
  const [refreshing,setRefreshing]= useState(false)
  const navigate                  = useNavigate()

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    try {
      const data = await scanService.listScans()
      setScans(data)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  // Auto-refresh every 5 seconds if any scan is running
  useEffect(() => {
    const hasRunning = scans.some(s =>
      s.status === 'running' || s.status === 'pending'
    )
    if (!hasRunning) return
    const interval = setInterval(() => load(true), 5000)
    return () => clearInterval(interval)
  }, [scans, load])

  const deleteScan = async (e, id) => {
    e.stopPropagation()
    if (!confirm('Delete this scan and all its results?')) return
    await scanService.deleteScan(id)
    load()
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-sky-500"/>
    </div>
  )

  const running = scans.filter(s => s.status === 'running' || s.status === 'pending')

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Scan History</h2>
          {running.length > 0 && (
            <p className="text-sky-400 text-xs mt-0.5 animate-pulse">
              {running.length} scan(s) running — auto-refreshing...
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

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-xs uppercase border-b border-gray-800">
              <th className="text-left py-2 pr-4">ID</th>
              <th className="text-left py-2 pr-4">Targets</th>
              <th className="text-left py-2 pr-4">Profile</th>
              <th className="text-left py-2 pr-4">Status</th>
              <th className="text-left py-2 pr-4">Progress</th>
              <th className="text-left py-2 pr-4">Created</th>
              <th className="text-left py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {scans.map(s => (
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
                <td className="py-2 pr-4">
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-gray-800 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full transition-all ${
                          s.status === 'completed' ? 'bg-green-500' :
                          s.status === 'failed'    ? 'bg-red-500'   : 'bg-sky-500'
                        }`}
                        style={{ width: `${s.progress ?? 0}%` }}
                      />
                    </div>
                    <span className="text-gray-500 text-xs">{s.progress ?? 0}%</span>
                  </div>
                </td>
                <td className="py-2 pr-4 text-gray-500 text-xs">
                  {s.created ? new Date(s.created).toLocaleString() : '—'}
                </td>
                <td className="py-2">
                  <button
                    onClick={e => deleteScan(e, s.scan_id)}
                    className="text-gray-600 hover:text-red-400 transition-colors p-1"
                  >
                    <Trash2 size={15}/>
                  </button>
                </td>
              </tr>
            ))}
            {!scans.length && (
              <tr>
                <td colSpan={7} className="py-12 text-center">
                  <p className="text-gray-500 mb-4">No scans yet</p>
                  <button
                    className="btn-primary"
                    onClick={() => navigate('/scan/new')}
                  >
                    + Start First Scan
                  </button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
