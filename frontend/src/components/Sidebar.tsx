import { Link, useLocation } from 'react-router-dom'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

const navItems: { path: string; label: string; icon: string; external?: boolean }[] = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/dashboard', label: 'Dashboard (Flask)', icon: '📈', external: true },
  { path: '/checkinout', label: 'Check In/Out', icon: '🔧', external: true },
  { path: '/reports', label: 'Reports', icon: '📋', external: true },
  { path: '/settings', label: 'Settings', icon: '⚙️', external: true },
  { path: '/logs', label: 'Logs', icon: '📜', external: true },
]

export default function Sidebar({ isOpen, onToggle }: SidebarProps) {
  const loc = useLocation()

  return (
    <aside
      className={`fixed left-0 top-0 z-40 h-screen bg-card/95 border-r border-border transition-all ${
        isOpen ? 'w-64' : 'w-16'
      }`}
    >
      <button
        onClick={onToggle}
        className="absolute -right-3 top-6 z-50 h-6 w-6 rounded-full border border-border bg-card shadow"
        aria-label={isOpen ? 'Close sidebar' : 'Open sidebar'}
      >
        {isOpen ? '←' : '→'}
      </button>
      <nav className="flex flex-col gap-1 p-4 pt-12">
        {navItems.map(({ path, label, icon, external }) => {
          const active = !external && (loc.pathname === path || (path !== '/' && loc.pathname.startsWith(path)))
          const cn = `flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${
            active ? 'bg-primary/20 text-primary' : 'text-muted-foreground hover:bg-muted'
          }`
          if (external) {
            return (
              <a key={path} href={path} className={cn}>
                <span>{icon}</span>
                {isOpen && <span>{label}</span>}
              </a>
            )
          }
          return (
            <Link key={path} to={path} className={cn}>
              <span>{icon}</span>
              {isOpen && <span>{label}</span>}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
