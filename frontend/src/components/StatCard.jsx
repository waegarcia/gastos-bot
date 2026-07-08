/**
 * Tarjeta de estadística simple.
 * label: string, value: string, sub: string (opcional)
 */
export default function StatCard({ label, value, sub }) {
  return (
    <div className="bg-white rounded-2xl shadow p-5 flex flex-col gap-1">
      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</span>
      <span className="text-2xl font-bold text-gray-800">{value}</span>
      {sub && <span className="text-xs text-gray-400">{sub}</span>}
    </div>
  )
}
