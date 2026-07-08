/**
 * Selector de mes. Muestra un <input type="month"> estilizado.
 * value: "YYYY-MM", onChange: fn(newValue)
 */
export default function MonthPicker({ value, onChange }) {
  return (
    <input
      type="month"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
    />
  )
}
