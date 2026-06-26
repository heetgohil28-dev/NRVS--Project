export default function MitreMatrix({ tactics = [] }) {
  if (!tactics.length) return (
    <div className="text-gray-500 text-sm text-center py-6">
      No MITRE ATT&CK data available
    </div>
  )

  return (
    <div className="flex flex-wrap gap-2">
      {tactics.map((t, i) => (
        <span
          key={i}
          className="bg-purple-900 text-purple-300 text-xs font-semibold px-3 py-1 rounded-lg border border-purple-800"
        >
          {t}
        </span>
      ))}
    </div>
  )
}
