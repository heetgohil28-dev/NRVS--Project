import { useEffect, useRef } from 'react'

export default function ScanProgress({
  progress = 0,
  status,
  message,
  logs = [],
  onStop
}) {
  const logRef = useRef(null)

  // Auto scroll log to bottom
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [logs])

  const statusColor = {
    pending:   'bg-gray-600',
    running:   'bg-sky-500',
    completed: 'bg-green-500',
    failed:    'bg-red-500',
  }

  const statusDot = {
    pending:   'bg-gray-500',
    running:   'bg-sky-400 animate-pulse',
    completed: 'bg-green-400',
    failed:    'bg-red-400',
  }

  const statusText = {
    pending:   'text-gray-400',
    running:   'text-sky-400',
    completed: 'text-green-400',
    failed:    'text-red-400',
  }

  return (
    <div className="flex flex-col gap-3">

      {/* Status Bar */}
      <div className="card">
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${statusDot[status] || 'bg-gray-500'}`}/>
            <span className={`text-sm font-semibold capitalize ${statusText[status] || 'text-gray-400'}`}>
              {status}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-sky-400 font-mono font-bold">{progress}%</span>
            {/* Stop button — only show when running */}
            {status === 'running' && onStop && (
              <button
                onClick={onStop}
                className="btn-danger text-xs px-3 py-1"
              >
                ⏹ Stop Scan
              </button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-800 rounded-full h-2.5 mb-3 overflow-hidden">
          <div
            className={`h-2.5 rounded-full transition-all duration-700 ${
              statusColor[status] || 'bg-sky-500'
            } ${status === 'running' ? 'relative' : ''}`}
            style={{ width: `${progress}%` }}
          >
            {status === 'running' && (
              <div className="absolute inset-0 bg-white opacity-20 animate-pulse rounded-full"/>
            )}
          </div>
        </div>

        {/* Current message */}
        {message && (
          <p className="text-xs text-gray-400 font-mono">{message}</p>
        )}
      </div>

      {/* Live Log Terminal */}
      {logs.length > 0 && (
        <div className="card bg-gray-950 border-gray-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">
              Live Scan Log
            </span>
            <span className="text-xs text-gray-600">{logs.length} events</span>
          </div>
          <div
            ref={logRef}
            className="h-48 overflow-y-auto font-mono text-xs flex flex-col gap-1 pr-1"
          >
            {logs.map((log, i) => (
              <div key={i} className="flex gap-2 items-start">
                <span className="text-gray-600 shrink-0">
                  {log.time}
                </span>
                <span className={
                  log.event === 'error'      ? 'text-red-400'   :
                  log.event === 'host_found' ? 'text-green-400' :
                  log.event === 'completed'  ? 'text-green-300' :
                  log.event === 'connected'  ? 'text-sky-400'   :
                  'text-gray-300'
                }>
                  {log.event === 'host_found'
                    ? `🖥  Host found: ${log.data?.ip || ''} — ${log.data?.ports || 0} ports`
                    : log.event === 'progress'
                    ? `⚡ ${log.message}`
                    : log.event === 'completed'
                    ? `✅ ${log.message}`
                    : log.event === 'error'
                    ? `❌ ${log.message}`
                    : log.event === 'connected'
                    ? `🔌 ${log.message}`
                    : log.message || log.event
                  }
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
