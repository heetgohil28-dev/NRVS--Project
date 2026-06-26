import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from 'recharts'

export default function PortFrequency({ ports = [] }) {
  if (!ports.length) return (
    <div className="text-gray-500 text-sm text-center py-8">No data available</div>
  )

  // Count port frequency
  const freq = {}
  ports.forEach(p => {
    const key = `${p.port}/${p.protocol}`
    freq[key] = (freq[key] || 0) + 1
  })

  const data = Object.entries(freq)
    .map(([port, count]) => ({ port, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937"/>
        <XAxis
          dataKey="port"
          tick={{ fill: '#9ca3af', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#9ca3af', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{ background: '#111827', border: '1px solid #1f2937' }}
          labelStyle={{ color: '#9ca3af' }}
        />
        <Bar dataKey="count" fill="#0ea5e9" radius={[4, 4, 0, 0]}/>
      </BarChart>
    </ResponsiveContainer>
  )
}
