import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

/**
 * Gráfico de barras de gastos por día del mes.
 * expenses: array de gastos del mes
 */
export default function DailyBarChart({ expenses }) {
  // Agrupar por día
  const totals = {}
  for (const e of expenses) {
    const day = e.date ? e.date.slice(8, 10) : '??'  // "YYYY-MM-DD" → "DD"
    totals[day] = (totals[day] || 0) + parseFloat(e.amount || 0)
  }

  const data = Object.entries(totals)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([day, total]) => ({ day: parseInt(day, 10), total: Math.round(total) }))

  if (data.length === 0) {
    return <p className="text-gray-400 text-sm text-center py-8">Sin datos</p>
  }

  const formatARS = (value) =>
    new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(value)

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="day" tick={{ fontSize: 12 }} label={{ value: 'Día', position: 'insideBottom', offset: -2 }} />
        <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
        <Tooltip formatter={(value) => formatARS(value)} labelFormatter={(label) => `Día ${label}`} />
        <Bar dataKey="total" fill="#6366f1" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
