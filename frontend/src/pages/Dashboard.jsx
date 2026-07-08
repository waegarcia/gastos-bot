import { useState, useEffect } from 'react'
import { getExpenses, currentMonth } from '../services/api'
import MonthPicker from '../components/MonthPicker'
import StatCard from '../components/StatCard'
import CategoryPieChart from '../components/CategoryPieChart'
import DailyBarChart from '../components/DailyBarChart'

export default function Dashboard() {
  const [month, setMonth] = useState(currentMonth())
  const [expenses, setExpenses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    getExpenses(month)
      .then(setExpenses)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [month])

  const formatARS = (value) =>
    new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(value)

  const total = expenses.reduce((sum, e) => sum + parseFloat(e.amount || 0), 0)
  const topCategory = (() => {
    const totals = {}
    for (const e of expenses) {
      const cat = e.category || 'OTROS'
      totals[cat] = (totals[cat] || 0) + parseFloat(e.amount || 0)
    }
    return Object.entries(totals).sort((a, b) => b[1] - a[1])[0]?.[0] ?? '—'
  })()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-800">Dashboard</h1>
        <MonthPicker value={month} onChange={setMonth} />
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          Error al cargar datos: {error}
        </div>
      )}

      {/* Stats */}
      {loading ? (
        <div className="text-gray-400 text-sm py-4">Cargando...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard
              label="Total del mes"
              value={formatARS(total)}
              sub={`${expenses.length} gastos registrados`}
            />
            <StatCard
              label="Categoría top"
              value={topCategory}
            />
            <StatCard
              label="Promedio por día"
              value={expenses.length > 0 ? formatARS(total / new Set(expenses.map(e => e.date)).size) : '—'}
              sub="días con gastos"
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl shadow p-5">
              <h2 className="text-sm font-medium text-gray-500 mb-4 uppercase tracking-wide">Por categoría</h2>
              <CategoryPieChart expenses={expenses} />
            </div>
            <div className="bg-white rounded-2xl shadow p-5">
              <h2 className="text-sm font-medium text-gray-500 mb-4 uppercase tracking-wide">Por día</h2>
              <DailyBarChart expenses={expenses} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
