import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { Sun, Moon, LogOut, User } from 'lucide-react'

export default function Navbar() {
  const { user, logout } = useAuth()
  const { dark, toggle } = useTheme()

  return (
    <header className="h-14 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-6">
      <h1 className="text-sky-400 font-bold tracking-widest text-sm uppercase">
        NRVS — Network & Vulnerability Scanner
      </h1>
      <div className="flex items-center gap-4">
        <button onClick={toggle} className="text-gray-400 hover:text-gray-100 transition-colors">
          {dark ? <Sun size={18}/> : <Moon size={18}/>}
        </button>
        <div className="flex items-center gap-2 text-gray-400 text-sm">
          <User size={16}/>
          <span>{user?.username}</span>
          <span className="bg-sky-900 text-sky-300 text-xs px-2 py-0.5 rounded-full">
            {user?.role}
          </span>
        </div>
        <button onClick={logout} className="text-gray-400 hover:text-red-400 transition-colors">
          <LogOut size={18}/>
        </button>
      </div>
    </header>
  )
}
