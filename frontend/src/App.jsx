import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { api } from './apiClient'
import Home from './Home'
import Login from './Login'
import Room from './Room'

export default function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getMe()
      .then((res) => {
        if (res.ok) {
          setUser(res.body)
        }
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Carregando...</div>
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route 
          path="/" 
          element={user ? <Home user={user} /> : <Navigate to="/login" replace />} 
        />
        <Route 
          path="/login" 
          element={!user ? <Login /> : <Navigate to="/" replace />} 
        />
        <Route
          path="/rooms/:code"
          element={user ? <Room user={user} /> : <Navigate to="/login" replace />}
        />
      </Routes>
    </BrowserRouter>
  )
}
