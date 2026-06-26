import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import Sidebar       from './components/Sidebar'
import Navbar        from './components/Navbar'
import Login         from './pages/Login'
import Register      from './pages/Register'
import Dashboard     from './pages/Dashboard'
import NewScan       from './pages/NewScan'
import ScanHistory   from './pages/ScanHistory'
import ScanDetails   from './pages/ScanDetails'
import AssetInventory from './pages/AssetInventory'
import CompareScans  from './pages/CompareScans'
import Reports       from './pages/Reports'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div className="flex items-center justify-center h-screen bg-gray-950">
      <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-sky-500"/>
    </div>
  )
  return user ? children : <Navigate to="/login" replace />
}

function AppLayout() {
  const { user } = useAuth()
  if (!user) return null
  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto p-6">
          <Routes>
            <Route path="/"        element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/scan/new" element={<PrivateRoute><NewScan /></PrivateRoute>} />
            <Route path="/scan/:id" element={<PrivateRoute><ScanDetails /></PrivateRoute>} />
            <Route path="/history"  element={<PrivateRoute><ScanHistory /></PrivateRoute>} />
            <Route path="/assets"   element={<PrivateRoute><AssetInventory /></PrivateRoute>} />
            <Route path="/compare"  element={<PrivateRoute><CompareScans /></PrivateRoute>} />
            <Route path="/reports"  element={<PrivateRoute><Reports /></PrivateRoute>} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <Routes>
          <Route path="/login"    element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/*"        element={<AppLayout />} />
        </Routes>
      </ThemeProvider>
    </AuthProvider>
  )
}
