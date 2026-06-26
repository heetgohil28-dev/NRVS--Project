import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Radar, History,
  GitCompare, Package, FileText, Plus
} from 'lucide-react'

const links = [
  { to: '/',              icon: LayoutDashboard, label: 'Dashboard'       },
  { to: '/scan/new',      icon: Plus,            label: 'New Scan'        },
  { to: '/scan/history',  icon: History,         label: 'Scan History'    },
  { to: '/scan/compare',  icon: GitCompare,      label: 'Compare Scans'   },
  { to: '/assets',        icon: Package,         label: 'Asset Inventory' },
  { to: '/reports',       icon: FileText,        label: 'Reports'         },
]

export default function Sidebar() {
  return (
    <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col py-6 gap-1">
      <div className="px-4 mb-6 flex items-center gap-2">
        <Radar size={22} className="text-sky-400"/>
        <span className="text-white font-bold text-lg">NRVS</span>
      </div>
      {links.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          className={({ isActive }) =>
            `flex items-center gap-3 px-4 py-2.5 mx-2 rounded-lg text-sm transition-colors ${
              isActive
                ? 'bg-sky-900 text-sky-300 font-semibold'
                : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'
            }`
          }
        >
          <Icon size={17}/>
          {label}
        </NavLink>
      ))}
    </aside>
  )
}
