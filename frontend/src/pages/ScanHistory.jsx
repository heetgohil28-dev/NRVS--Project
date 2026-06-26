import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { scanService } from '../services/scanService'
import { Trash2 } from 'lucide-react'

export default function ScanHistory() {
  const [scans,   setScans]   = useState([])
  const [loading, setLoading] = useState(true)
  const navigate              = useNavigate()

  const load = () => {
    scanService.listScans()
      .then(setScans)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const deleteScan = async (e, id) => {
    e.stopPropagation()
    if (!confirm('Delete this scan?')) return
    await scanService.deleteScan(id)
    load()
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-sky-500"/>
    </div>
  )

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Scan History</h2>
        <button className="btn-primary" onClick={() => navigate('/scan/new')}>
          + New Scan
        </button>
      </div>
      <div className="card">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-xs uppercase border-b border-gray-800">
              <th className="text-left py-2 pr-4">ID</th>
              <th className="text-left py-2 pr-4">Targets</th>
              <th className="text-left py-2 pr-4">Profile</th>
              <th className="text-left py-2 pr-4">Status</th>
              <th className="text-left py-2 pr-4">Progress</th>
              <th className="text-left py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {scans.map(s => (
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
                <td className="py-2 pr-4 text-gray-400">{s.progress}%</td>
                <td className="py-2">
                  <button
                    onClick={e => deleteScan(e, s.scan_id)}
                    className="text-gray-600 hover:text-red-400 transition-colors">
                    <Trash2 size={15}/>
                  </button>
                </td>
              </tr>
            ))}
            {!scans.length && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-gray-500">
                  No scans yet — start one!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
