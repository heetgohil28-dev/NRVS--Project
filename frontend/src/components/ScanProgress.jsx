export default function ScanProgress({ progress = 0, status, message }) {
  const statusColor = {
    pending:   'bg-gray-600',
    running:   'bg-sky-500',
    completed: 'bg-green-500',
    failed:    'bg-red-500',
  }

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-semibold text-gray-300 capitalize">{status}</span>
        <span className="text-sm text-sky-400 font-mono">{progress}%</span>
      </div>
      <div className="w-full bg-gray-800 rounded-full h-2 mb-3">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${statusColor[status] || 'bg-sky-500'}`}
          style={{ width: `${progress}%` }}
        />
      </div>
      {message && (
        <p className="text-xs text-gray-400">{message}</p>
      )}
    </div>
  )
}
