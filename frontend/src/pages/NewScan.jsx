import { useState } from 'react'
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
  const navigate                   = useNavigate()
  const [targets,    setTargets]   = useState('')
  const [profile,    setProfile]   = useState('standard')
  const [customArgs, setCustomArgs]= useState('')
  const [showCustom, setShowCustom]= useState(false)
  const [error,      setError]     = useState('')
  const [loading,    setLoading]   = useState(false)
  const [scan,       setScan]      = useState(null)
  const [progress,   setProgress]  = useState({ progress: 0, status: 'pending', message: '' })

  const handle = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const targetList = targets.split('\n').map(t => t.trim()).filter(Boolean)
      if (!targetList.length) throw new Error('Enter at least one target')
      const res = await scanService.startScan(targetList, profile, customArgs)
      setScan(res)

      const ws = scanService.connectWebSocket(res.scan_id, data => {
        if (data.event === 'progress') {
          setProgress({ progress: data.progress, status: data.status, message: data.message })
          if (data.status === 'completed') {
            ws.close()
            setTimeout(() => navigate(`/scan/${res.scan_id}`), 1500)
          }
          if (data.status === 'failed') ws.close()
        }
      })
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Scan failed')
    } finally {
      setLoading(false)
    }
  }

  if (scan) return (
    <div className="max-w-xl mx-auto flex flex-col gap-4">
      <h2 className="text-xl font-bold text-white">Scan #{scan.scan_id} Running</h2>
      <ScanProgress {...progress}/>
      <p className="text-gray-500 text-sm">
        Scanning {scan.expanded_count} host(s) — redirecting when complete...
      </p>
    </div>
  )

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
            Targets <span className="text-gray-600">(one per line — IPs, CIDRs, hostnames)</span>
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

        {/* Custom Args Toggle */}
        <div>
          <button
            type="button"
            onClick={() => setShowCustom(s => !s)}
            className="text-sky-400 text-sm hover:underline"
          >
            {showCustom ? '▼' : '▶'} Custom Nmap Flags (advanced)
          </button>

          {showCustom && (
            <div className="mt-3 flex flex-col gap-2">
              <input
                className="input font-mono"
                placeholder="e.g. -p 80,443 -T3 --script=http-title"
                value={customArgs}
                onChange={e => setCustomArgs(e.target.value)}
                maxLength={200}
              />
              <div className="text-gray-600 text-xs">
                Examples — click to use:
              </div>
              <div className="flex flex-wrap gap-2">
                {EXAMPLES.map(ex => (
                  <button
                    key={ex}
                    type="button"
                    onClick={() => setCustomArgs(ex)}
                    className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-400 px-2 py-1 rounded font-mono transition-colors"
                  >
                    {ex}
                  </button>
                ))}
              </div>
              <p className="text-gray-600 text-xs">
                ⚠️ Dangerous flags like output redirects, file inputs, and exploit scripts are blocked.
              </p>
            </div>
          )}
        </div>

        <button className="btn-primary w-full" disabled={loading}>
          {loading ? 'Starting...' : 'Start Scan'}
        </button>
      </form>
    </div>
  )
}
