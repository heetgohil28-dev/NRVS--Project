export default function ScoreCard({ title, value, sub, color = 'sky' }) {
  const colors = {
    sky:    'text-sky-400',
    red:    'text-red-400',
    orange: 'text-orange-400',
    green:  'text-green-400',
    yellow: 'text-yellow-400',
  }
  return (
    <div className="card flex flex-col gap-1">
      <span className="text-gray-400 text-xs uppercase tracking-wider">{title}</span>
      <span className={`text-3xl font-bold ${colors[color] || colors.sky}`}>{value}</span>
      {sub && <span className="text-gray-500 text-xs">{sub}</span>}
    </div>
  )
}
