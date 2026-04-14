import { NavLink, Outlet } from 'react-router-dom'

const tabs = [
  { to: '/scan', label: 'Scan' },
  { to: '/results', label: 'Results' },
  { to: '/history', label: 'History' },
]

export default function NavShell() {
  return (
    <div className="scanner-shell">
      <header className="scanner-header">
        <div>
          <p className="scanner-kicker">Solidity Vulnerability Scanner</p>
          <h1>Security Console</h1>
        </div>
        <nav className="scanner-nav" aria-label="Scanner sections">
          {tabs.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              className={({ isActive }) => (isActive ? 'is-active' : undefined)}
            >
              {tab.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="scanner-main">
        <Outlet />
      </main>
    </div>
  )
}
