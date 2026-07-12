import { useState, useEffect } from 'react'
import { getExpenses, currentMonth } from '../services/api'
import MonthPicker from '../components/MonthPicker'

const CATEGORY_COLORS = {
  ALIMENTACION: 'bg-green-100 text-green-700',
  TRANSPORTE:   'bg-blue-100 text-blue-700',
  SALUD:        'bg-red-100 text-red-700',
  ENTRETENIMIENTO: 'bg-purple-100 text-purple-700',
  HOGAR:        'bg-yellow-100 text-yellow-700',
  ROPA:         'bg-pink-100 text-pink-700',
  EDUCACION:    'bg-indigo-100 text-indigo-700',
  RESTAURANTE:  'bg-orange-100 text-orange-700',
  SERVICIOS:    'bg-teal-100 text-teal-700',
  MASCOTAS:     'bg-lime-100 text-lime-700',
  AUTOMOVIL:    'bg-cyan-100 text-cyan-700',
  OTROS:        'bg-gray-100 text-gray-600',
}

export default function ExpenseList() {
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
    new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(parseFloat(value))

  const formatDate = (dateStr) => {
    const [year, month, day] = dateStr.split('-')
    return `${day}/${month}/${year}`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-800">Gastos</h1>
        <MonthPicker value={month} onChange={setMonth} />
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          Error al cargar datos: {error}
        </div>
      )}

      {/* Tabla */}
      {loading ? (
        <div className="text-gray-400 text-sm py-4">Cargando...</div>
      ) : expenses.length === 0 ? (
        <div className="bg-white rounded-2xl shadow p-8 text-center text-gray-400 text-sm">
          No hay gastos registrados para este mes.
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-100">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Fecha</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Lugar</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Categoría</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Cargado por</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wide">Monto</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {expenses.map((e) => (
                <tr key={e.expense_id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                    {formatDate(e.date)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-800 font-medium">
                    {e.place}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full ${CATEGORY_COLORS[e.category] ?? CATEGORY_COLORS.OTROS}`}>
                      {e.category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                    {e.logged_by || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm font-semibold text-gray-800 text-right whitespace-nowrap">
                    {formatARS(e.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50 border-t border-gray-200">
              <tr>
                <td colSpan={4} className="px-4 py-3 text-sm font-medium text-gray-500">
                  {expenses.length} gastos
                </td>
                <td className="px-4 py-3 text-sm font-bold text-gray-800 text-right">
                  {formatARS(expenses.reduce((sum, e) => sum + parseFloat(e.amount || 0), 0))}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  )
}
