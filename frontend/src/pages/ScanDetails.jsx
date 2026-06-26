import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { scanService } from '../services/scanService'
import { reportService } from '../services/reportService'
import HostCard from '../components/HostCard'
import RiskDistribution from '../charts/RiskDistribution'
import PortFrequency from '../charts/PortFrequency'

export default function ScanDetails() {
  const { id }                  = useParams()
  const navigate                = useNavigate()
  const [scan,    setScan]      = useState(null)
  const [results, setResults]   = useState(null)
  const [loading, setLoading]   = useState(true)
  const [reporting,setReporting]= useState(false)

  useEffect(() => {
    scanService.getScan(id).then(setScan)
    scanService.getScanResults(id)
      .then(setResults)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  const generateReport = async type => {
    setReporting(true)
    try {
      await reportService.generateReport(Number(id), type)
      alert(`${type.toUpperCase()} report queued successfully!`)
    } catch (err) {
      alert(err.response?.data?.detail || 'Report generation failed')
    } finally {
      setReporting(false)
    }
  }

  // Collect all ports for frequency chart
  const allPorts = results?.hosts?.flatMap(h => h.ports) || []

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-sky-500"/>
    </div>
  )

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Scan #{id}</h2>
          <p className="text-gray-500 text-sm">
            {scan?.targets?.join(', ')} — {scan?.profile} profile
          </p>
        </div>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={() => navigate('/scan/history')}>
            ← Back
          </button>
          <button
            className="btn-primary"
            disabled={reporting || scan?.status !== 'completed'}
            onClick={() => generateReport('pdf')}>
            {reporting ? 'Generating...' : 'Export PDF'}
          </button>
        </div>
      </div>

      {/* Status */}
      <div className="card flex gap-6 text-sm">
        <div>
          <span className="text-gray-500">Status </span>
          <span className={`font-semibold ${
            scan?.status === 'completed' ? 'text-green-400' :
            scan?.status === 'failed'    ? 'text-red-400'   : 'text-sky-400'
          }`}>{scan?.status}</span>
        </div>
        <div>
          <span className="text-gray-500">Hosts </span>
          <span className="text-white font-semibold">{results?.total_hosts || 0}</span>
        </div>
        <div>
          <span className="text-gray-500">Progress </span>
          <span className="text-white font-semibold">{scan?.progress}%</span>
        </div>
      </div>

      {results && (
        <>
          {/* Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-300 mb-4">Port Frequency</h3>
              <PortFrequency ports={allPorts}/>
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

          {/* Hosts */}
          <div>
            <h3 className="text-sm font-semibold text-gray-300 mb-3">
              Hosts Found ({results.total_hosts})
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.hosts.map((h, i) => (
                <HostCard key={i} host={h}/>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
