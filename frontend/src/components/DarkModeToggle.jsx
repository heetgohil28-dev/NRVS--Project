import { useTheme } from '../context/ThemeContext'
import { Sun, Moon } from 'lucide-react'

export default function DarkModeToggle() {
  const { dark, toggle } = useTheme()
  return (
    <button
      onClick={toggle}
      className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-gray-100 transition-colors"
    >
      {dark ? <Sun size={16}/> : <Moon size={16}/>}
    </button>
  )
}
