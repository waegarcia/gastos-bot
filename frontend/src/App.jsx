import { useState, useEffect } from 'react'
import { getCurrentUser, signOut } from 'aws-amplify/auth'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import ExpenseList from './pages/ExpenseList'

const NAV = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'list',      label: 'Gastos' },
]

export default function App() {
  const [page, setPage] = useState('dashboard')
  const [authChecked, setAuthChecked] = useState(false)
  const [signedIn, setSignedIn] = useState(false)

  useEffect(() => {
    getCurrentUser()
      .then(() => setSignedIn(true))
      .catch(() => setSignedIn(false))
      .finally(() => setAuthChecked(true))
  }, [])

  async function handleSignOut() {
    await signOut()
    setSignedIn(false)
  }

  if (!authChecked) return null
  if (!signedIn) return <Login onSignedIn={() => setSignedIn(true)} />

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-4 flex items-center h-14 gap-6">
          <span className="font-bold text-indigo-600 text-lg tracking-tight">💸 Gastos Bot</span>
          <div className="flex gap-1 flex-1">
            {NAV.map((item) => (
              <button
                key={item.id}
                onClick={() => setPage(item.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  page === item.id
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-gray-500 hover:text-gray-800 hover:bg-gray-100'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
          <button
            onClick={handleSignOut}
            className="text-sm text-gray-500 hover:text-gray-800"
          >
            Salir
          </button>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        {page === 'dashboard' && <Dashboard />}
        {page === 'list' && <ExpenseList />}
      </main>
    </div>
  )
}
