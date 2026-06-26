import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Radar } from 'lucide-react'

export default function Login() {
  const { login }            = useAuth()
  const navigate             = useNavigate()
  const [form, setForm]      = useState({ username: '', password: '' })
  const [error, setError]    = useState('')
  const [loading, setLoading]= useState(false)

  const handle = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.username, form.password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <Radar size={40} className="text-sky-400 mb-3"/>
          <h1 className="text-2xl font-bold text-white">NRVS</h1>
          <p className="text-gray-500 text-sm">Network & Vulnerability Scanner</p>
        </div>
        <form onSubmit={handle} className="card flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-white">Sign In</h2>
          {error && (
            <div className="bg-red-900 border border-red-700 text-red-300 text-sm px-3 py-2 rounded-lg">
              {error}
            </div>
          )}
          <div>
            <label className="text-gray-400 text-sm mb-1 block">Username</label>
            <input
              className="input"
              type="text"
              placeholder="Enter username"
              value={form.username}
              onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
              required
            />
          </div>
          <div>
            <label className="text-gray-400 text-sm mb-1 block">Password</label>
            <input
              className="input"
              type="password"
              placeholder="Enter password"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              required
            />
          </div>
          <button className="btn-primary w-full" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
          <p className="text-center text-gray-500 text-sm">
            No account?{' '}
            <Link to="/register" className="text-sky-400 hover:underline">Register</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
