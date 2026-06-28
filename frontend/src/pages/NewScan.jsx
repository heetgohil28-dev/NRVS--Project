import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { scanService } from '../services/scanService'
import ScanProgress from '../components/ScanProgress'

const PROFILES = [
  { value: 'quick',    label: 'Quick',    desc: 'Fast scan, top ports only'     },
  { value: 'standard', label: 'Standard', desc: 'Service & OS detection'        },
  { value: 'deep',     label: 'Deep',     desc: 'Full port scan, all detection' },
  { value: 'stealth',  label: 'Stealth',  desc: 'Slow, low-noise scan'          },
  { value: 'vuln',     label: 'Vuln',     desc: 'Vulnerability scripts'         },
  { value: 'udp',      label: 'UDP',      desc: 'UDP port scan'                 },
]

const EXAMPLES = [
  '-p 80,443,8080',
  '-p 1-1000',
  '-T3',
  '--script=http-title',
  '--open -sV',
  '--min-rate 1000',
]

export default function NewScan() {
  const navigate                     = useNavigate()
  const wsRef                        = useRef(null)
  const [targets,    setTargets]     = useState('')
  const [profile,    setProfile]     = useState('standard')
  const [extraArgs,  setExtraArgs]   = useState('')
  const [showCustom, setShowCustom]  = useState(false)
  const [error,      setError]       = useState('')
  const [loading,    setLoading]     = useState(false)
  const [scan,       setScan]        = useState(null)
  const [progress,   setProgress]    = useState({
    progress: 0,
    status:   'pending',
    message:  'Waiting to start...'
  })
  const [logs,       setLogs]        = useState([])
  const [stopped,    setStopped]     = useState(false)

  // Add a log entry with timestamp
  const addLog = (data) => {
    setLogs(prev => [...prev, {
      ...data,
      time: new Date().toLocaleTimeString('en-US', {
        hour:   '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
    }])
  }

  // Stop scan handler
  const handleStop = async () => {
    if (!scan) return
    if (!confirm('Are you sure you want to stop this scan?')) return

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    try {
      await scanService.stopScan(scan.scan_id)
    } catch (err) {
      console.error('Stop scan error:', err)
    }

    setStopped(true)
    setProgress(p => ({ ...p, status: 'failed', message: 'Scan stopped by user' }))
    addLog({ event: 'error', message: 'Scan stopped by user' })
  }

  const handle = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    setLogs([])
    setStopped(false)

    try {
      const targetList = targets
        .split('\n')
        .map(t => t.trim())
        .filter(Boolean)

      if (!targetList.length) throw new Error('Enter at least one target')

      const res = await scanService.startScan(targetList, profile, extraArgs)
      setScan(res)
      setProgress({ progress: 0, status: 'pending', message: 'Scan queued...' })

      // Connect WebSocket
      const ws = scanService.connectWebSocket(res.scan_id, {
        onOpen: () => {
          addLog({ event: 'connected', message: `Connected to scan #${res.scan_id}` })
        },

        onMessage: data => {
          if (data.event === 'progress') {
            setProgress({
              progress: data.progress,
              status:   data.status,
              message:  data.message,
            })
            addLog({ event: data.status, message: data.message })

            if (data.status === 'completed') {
              ws.close()
              wsRef.current = null
              setTimeout(() => navigate(`/scan/${res.scan_id}`), 2000)
            }
            if (data.status === 'failed') {
              ws.close()
              wsRef.current = null
            }
          }

          if (data.event === 'host_found') {
            addLog({ event: 'host_found', message: data.message, data: data.host })
          }

          if (data.event === 'error') {
            addLog({ event: 'error', message: data.message })
            setProgress(p => ({ ...p, status: 'failed', message: data.message }))
          }
        },

        onError: () => {
          addLog({ event: 'error', message: 'WebSocket connection error' })
          setProgress(p => ({ ...p, status: 'failed', message: 'Connection lost' }))
        },

        onClose: () => {
          if (!stopped) {
            addLog({ event: 'error', message: 'WebSocket disconnected' })
          }
        }
      })

      wsRef.current = ws

    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Scan failed to start')
    } finally {
      setLoading(false)
    }
  }

  // ── Scan Running View ─────────────────────────────────
  if (scan) return (
    <div className="max-w-2xl mx-auto flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Scan #{scan.scan_id}</h2>
          <p className="text-gray-500 text-sm">
            {scan.expanded_count} host(s) — {profile} profile
            {extraArgs && <span className="text-gray-600"> — {extraArgs}</span>}
          </p>
        </div>
        {progress.status === 'completed' && (
          <span className="text-green-400 text-sm font-semibold">
            ✅ Redirecting to results...
          </span>
        )}
      </div>

      <ScanProgress
        progress={progress.progress}
        status={progress.status}
        message={progress.message}
        logs={logs}
        onStop={progress.status === 'running' ? handleStop : null}
      />

      {progress.status === 'failed' && !stopped && (
        <div className="flex gap-3">
          <button
            className="btn-primary"
            onClick={() => { setScan(null); setLogs([]) }}
          >
            Try Again
          </button>
          <button
            className="btn-ghost"
            onClick={() => navigate('/scan/history')}
          >
            View History
          </button>
        </div>
      )}

      {stopped && (
        <div className="flex gap-3">
          <button
            className="btn-primary"
            onClick={() => { setScan(null); setLogs([]); setStopped(false) }}
          >
            Start New Scan
          </button>
          <button
            className="btn-ghost"
            onClick={() => navigate('/scan/history')}
          >
            View History
          </button>
        </div>
      )}
    </div>
  )

  // ── Scan Form View ────────────────────────────────────
  return (
    <div className="max-w-xl mx-auto">
      <h2 className="text-xl font-bold text-white mb-6">New Scan</h2>
      <form onSubmit={handle} className="card flex flex-col gap-5">

        {error && (
          <div className="bg-red-900 border border-red-700 text-red-300 text-sm px-3 py-2 rounded-lg">
            {error}
          </div>
        )}

        {/* Targets */}
        <div>
          <label className="text-gray-400 text-sm mb-1 block">
            Targets
            <span className="text-gray-600 ml-1">(one per line — IPs, CIDRs, hostnames)</span>
          </label>
          <textarea
            className="input font-mono h-32 resize-none"
            placeholder={"192.168.1.1\n10.0.0.0/24\nscanme.nmap.org"}
            value={targets}
            onChange={e => setTargets(e.target.value)}
            required
          />
        </div>

        {/* Profiles */}
        <div>
          <label className="text-gray-400 text-sm mb-2 block">Scan Profile</label>
          <div className="grid grid-cols-2 gap-2">
            {PROFILES.map(p => (
              <button
                key={p.value}
                type="button"
                onClick={() => setProfile(p.value)}
                className={`text-left px-3 py-2 rounded-lg border text-sm transition-colors ${
                  profile === p.value
                    ? 'border-sky-500 bg-sky-900 text-sky-200'
                    : 'border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600'
                }`}
              >
                <div className="font-semibold">{p.label}</div>
                <div className="text-xs opacity-70">{p.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Custom Nmap Flags */}
        <div>
          <button
            type="button"
            onClick={() => setShowCustom(s => !s)}
            className="text-sky-400 text-sm hover:underline flex items-center gap-1"
          >
            <span>{showCustom ? '▼' : '▶'}</span>
            <span>Custom Nmap Flags (advanced)</span>
          </button>

          {showCustom && (
            <div className="mt-3 flex flex-col gap-2">
              <input
                className="input font-mono"
                placeholder="e.g. -p 80,443 -T3 --script=http-title"
                value={extraArgs}
                onChange={e => setExtraArgs(e.target.value)}
                maxLength={200}
              />
              <p className="text-gray-600 text-xs">
                Quick examples — click to use:
              </p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLES.map(ex => (
                  <button
                    key={ex}
                    type="button"
                    onClick={() => setExtraArgs(ex)}
                    className={`text-xs px-2 py-1 rounded font-mono transition-colors border ${
                      extraArgs === ex
                        ? 'bg-sky-900 border-sky-600 text-sky-300'
                        : 'bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700'
                    }`}
                  >
                    {ex}
                  </button>
                ))}
              </div>
              <p className="text-yellow-700 text-xs">
                ⚠️ Dangerous flags (output redirects, file inputs, exploit scripts) are blocked by the server.
              </p>
            </div>
          )}
        </div>

        <button className="btn-primary w-full text-base py-3" disabled={loading}>
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin rounded-full h-4 w-4 border-t-2 border-white"/>
              Starting scan...
            </span>
          ) : '🔍 Start Scan'}
        </button>

      </form>
    </div>
  )
}
