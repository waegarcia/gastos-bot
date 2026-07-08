import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const COLORS = [
  '#6366f1', '#f59e0b', '#10b981', '#ef4444', '#3b82f6',
  '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#84cc16',
  '#06b6d4', '#a78bfa',
]

/**
 * Gráfico de torta de gastos por categoría.
 * expenses: array de gastos del mes
 */
export default function CategoryPieChart({ expenses }) {
  // Agrupar por categoría
  const totals = {}
  for (const e of expenses) {
    const cat = e.category || 'OTROS'
    totals[cat] = (totals[cat] || 0) + parseFloat(e.amount || 0)
  }

  const data = Object.entries(totals)
    .map(([name, value]) => ({ name, value: Math.round(value) }))
    .sort((a, b) => b.value - a.value)

  if (data.length === 0) {
    return <p className="text-gray-400 text-sm text-center py-8">Sin datos</p>
  }

  const formatARS = (value) =>
    new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(value)

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={110}
          paddingAngle={3}
          dataKey="value"
        >
          {data.map((_, index) => (
            <Cell key={index} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => formatARS(value)} />
        <Legend formatter={(value) => value} />
      </PieChart>
    </ResponsiveContainer>
  )
}
