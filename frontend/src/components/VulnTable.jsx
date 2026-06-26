import CVEBadge from './CVEBadge'

export default function VulnTable({ vulns = [] }) {
  if (!vulns.length) return (
    <div className="text-gray-500 text-sm text-center py-8">
      No vulnerabilities found
    </div>
  )

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-500 text-xs uppercase border-b border-gray-800">
            <th className="text-left py-2 pr-4">CVE ID</th>
            <th className="text-left py-2 pr-4">Severity</th>
            <th className="text-left py-2 pr-4">CVSS</th>
            <th className="text-left py-2">Description</th>
          </tr>
        </thead>
        <tbody>
          {vulns.map((v, i) => (
            <tr key={i} className="border-b border-gray-800 hover:bg-gray-800 transition-colors">
              <td className="py-2 pr-4 font-mono text-sky-400">{v.cve_id}</td>
              <td className="py-2 pr-4"><CVEBadge severity={v.severity}/></td>
              <td className="py-2 pr-4 text-gray-300">{v.cvss_v3_score || v.cvss_v2_score || '—'}</td>
              <td className="py-2 text-gray-400 truncate max-w-xs">{v.description || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
