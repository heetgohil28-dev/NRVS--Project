import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authService } from '../services/authService'
import { Radar } from 'lucide-react'

export default function Register() {
  const navigate              = useNavigate()
  const [form, setForm]       = useState({ username: '', email: '', password: '', role: 'analyst' })
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  const handle = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await authService.register(form)
      navigate('/login')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
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
          <p className="text-gray-500 text-sm">Create your account</p>
        </div>
        <form onSubmit={handle} className="card flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-white">Register</h2>
          {error && (
            <div className="bg-red-900 border border-red-700 text-red-300 text-sm px-3 py-2 rounded-lg">
              {error}
            </div>
          )}
          <div>
            <label className="text-gray-400 text-sm mb-1 block">Username</label>
            <input className="input" type="text" placeholder="username"
              value={form.username}
              onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
              required/>
          </div>
          <div>
            <label className="text-gray-400 text-sm mb-1 block">Email</label>
            <input className="input" type="email" placeholder="you@example.com"
              value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              required/>
          </div>
          <div>
            <label className="text-gray-400 text-sm mb-1 block">Password</label>
            <input className="input" type="password" placeholder="Min 8 chars, upper, lower, number, symbol"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              required/>
          </div>
          <div>
            <label className="text-gray-400 text-sm mb-1 block">Role</label>
            <select className="input" value={form.role}
              onChange={e => setForm(f => ({ ...f, role: e.target.value }))}>
              <option value="analyst">Analyst</option>
              <option value="admin">Admin</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
          <button className="btn-primary w-full" disabled={loading}>
            {loading ? 'Creating account...' : 'Register'}
          </button>
          <p className="text-center text-gray-500 text-sm">
            Already have an account?{' '}
            <Link to="/login" className="text-sky-400 hover:underline">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
