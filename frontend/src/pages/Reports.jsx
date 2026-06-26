import { useState, useEffect } from 'react'
import { reportService } from '../services/reportService'
import { Trash2, FileText } from 'lucide-react'

export default function Reports() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    reportService.listReports()
      .then(setReports)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const deleteReport = async id => {
    if (!confirm('Delete this report?')) return
    await reportService.deleteReport(id)
    load()
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-sky-500"/>
    </div>
  )

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-bold text-white">Reports</h2>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-xs uppercase border-b border-gray-800">
              <th className="text-left py-2 pr-4">ID</th>
              <th className="text-left py-2 pr-4">Scan</th>
              <th className="text-left py-2 pr-4">Type</th>
              <th className="text-left py-2 pr-4">Hosts</th>
              <th className="text-left py-2 pr-4">Vulns</th>
              <th className="text-left py-2 pr-4">Critical</th>
              <th className="text-left py-2 pr-4">Created</th>
              <th className="text-left py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {reports.map(r => (
              <tr key={r.report_id} className="border-b border-gray-800 hover:bg-gray-800 transition-colors">
                <td className="py-2 pr-4 text-sky-400 font-mono">#{r.report_id}</td>
                <td className="py-2 pr-4 text-gray-300">#{r.scan_id}</td>
                <td className="py-2 pr-4">
                  <span className="flex items-center gap-1 text-gray-400">
                    <FileText size={13}/> {r.report_type?.toUpperCase()}
                  </span>
                </td>
                <td className="py-2 pr-4 text-gray-300">{r.total_hosts}</td>
                <td className="py-2 pr-4 text-gray-300">{r.total_vulns}</td>
                <td className="py-2 pr-4">
                  <span className="badge-critical">{r.critical}</span>
                </td>
                <td className="py-2 pr-4 text-gray-500 text-xs">
                  {r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}
                </td>
                <td className="py-2">
                  <button
                    onClick={() => deleteReport(r.report_id)}
                    className="text-gray-600 hover:text-red-400 transition-colors">
                    <Trash2 size={15}/>
                  </button>
                </td>
              </tr>
            ))}
            {!reports.length && (
              <tr>
                <td colSpan={8} className="py-8 text-center text-gray-500">
                  No reports yet — generate one from a scan!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
