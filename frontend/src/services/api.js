import { fetchAuthSession } from 'aws-amplify/auth'

// La URL base se toma de la variable de entorno VITE_API_BASE.
// En local: crear un archivo .env en frontend/ con:
//   VITE_API_BASE=https://<tu-api-id>.execute-api.<region>.amazonaws.com/prod
const API_BASE = import.meta.env.VITE_API_BASE

if (!API_BASE) {
  console.error('VITE_API_BASE no está definida. Creá frontend/.env con la URL de tu API Gateway.')
}

/**
 * Obtiene gastos. Si se pasa month (formato "YYYY-MM"), filtra por mes.
 * @param {string|null} month - Ej: "2026-07"
 * @returns {Promise<Array>}
 */
export async function getExpenses(month = null) {
  const url = month
    ? `${API_BASE}/expenses?month=${month}`
    : `${API_BASE}/expenses`

  const { tokens } = await fetchAuthSession()
  const res = await fetch(url, {
    headers: { Authorization: tokens.idToken.toString() },
  })
  if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`)
  return res.json()
}

/**
 * Devuelve el mes actual en formato "YYYY-MM"
 */
export function currentMonth() {
  const now = new Date()
  const yyyy = now.getFullYear()
  const mm = String(now.getMonth() + 1).padStart(2, '0')
  return `${yyyy}-${mm}`
}
