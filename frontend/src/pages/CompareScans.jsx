import { useState } from 'react'
import { scanService } from '../services/scanService'

export default function CompareScans() {
  const [scanA,   setScanA]   = useState('')
  const [scanB,   setScanB]   = useState('')
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  const handle = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await scanService.compareScans(scanA, scanB)
      setResult(res)
    } catch (err) {
      setError(err.response?.data?.detail || 'Comparison failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-6 max-w-3xl">
      <h2 className="text-xl font-bold text-white">Compare Scans</h2>
      <form onSubmit={handle} className="card flex gap-4 items-end">
        <div className="flex-1">
          <label className="text-gray-400 text-sm mb-1 block">Scan ID A</label>
          <input className="input" type="number" placeholder="e.g. 1"
            value={scanA} onChange={e => setScanA(e.target.value)} required/>
        </div>
        <div className="flex-1">
          <label className="text-gray-400 text-sm mb-1 block">Scan ID B</label>
          <input className="input" type="number" placeholder="e.g. 2"
            value={scanB} onChange={e => setScanB(e.target.value)} required/>
        </div>
        <button className="btn-primary" disabled={loading}>
          {loading ? 'Comparing...' : 'Compare'}
        </button>
      </form>

      {error && (
        <div className="bg-red-900 border border-red-700 text-red-300 text-sm px-3 py-2 rounded-lg">
          {error}
        </div>
      )}

      {result && (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="card text-center">
              <span className="text-gray-500 text-xs">Hosts Added</span>
              <span className="text-2xl font-bold text-green-400">{result.summary.hosts_added}</span>
            </div>
            <div className="card text-center">
              <span className="text-gray-500 text-xs">Hosts Removed</span>
              <span className="text-2xl font-bold text-red-400">{result.summary.hosts_removed}</span>
            </div>
            <div className="card text-center">
              <span className="text-gray-500 text-xs">Risk Changed</span>
              <span className="text-2xl font-bold text-yellow-400">{result.summary.hosts_changed}</span>
            </div>
          </div>

          {result.new_hosts.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-semibold text-green-400 mb-3">New Hosts</h3>
              {result.new_hosts.map((ip, i) => (
                <div key={i} className="font-mono text-sm text-gray-300 py-1">{ip}</div>
              ))}
            </div>
          )}

          {result.removed_hosts.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-semibold text-red-400 mb-3">Removed Hosts</h3>
              {result.removed_hosts.map((ip, i) => (
                <div key={i} className="font-mono text-sm text-gray-300 py-1">{ip}</div>
              ))}
            </div>
          )}

          {result.risk_changes.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-semibold text-yellow-400 mb-3">Risk Changes</h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 text-xs uppercase border-b border-gray-800">
                    <th className="text-left py-2 pr-4">IP</th>
                    <th className="text-left py-2 pr-4">Old Score</th>
                    <th className="text-left py-2 pr-4">New Score</th>
                    <th className="text-left py-2">Delta</th>
                  </tr>
                </thead>
                <tbody>
                  {result.risk_changes.map((r, i) => (
                    <tr key={i} className="border-b border-gray-800">
                      <td className="py-2 pr-4 font-mono text-sky-400">{r.ip}</td>
                      <td className="py-2 pr-4 text-gray-300">{r.old_score}</td>
                      <td className="py-2 pr-4 text-gray-300">{r.new_score}</td>
                      <td className={`py-2 font-semibold ${r.delta > 0 ? 'text-red-400' : 'text-green-400'}`}>
                        {r.delta > 0 ? '+' : ''}{r.delta}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
