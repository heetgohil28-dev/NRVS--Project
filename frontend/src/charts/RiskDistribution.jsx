import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const COLORS = ['#ef4444', '#f97316', '#eab308', '#3b82f6', '#6b7280']

export default function RiskDistribution({ data = [] }) {
  if (!data.length) return (
    <div className="text-gray-500 text-sm text-center py-8">No data available</div>
  )
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="severity"
          cx="50%"
          cy="50%"
          outerRadius={90}
          label={({ severity, percent }) =>
            `${severity} ${(percent * 100).toFixed(0)}%`
          }
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]}/>
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: '#111827', border: '1px solid #1f2937' }}
          labelStyle={{ color: '#9ca3af' }}
        />
        <Legend/>
      </PieChart>
    </ResponsiveContainer>
  )
}
