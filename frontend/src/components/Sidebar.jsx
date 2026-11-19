import { LayoutDashboard, Users, Package, ShoppingCart, Receipt, Truck,
         ClipboardCheck, BarChart3, Sparkles, Sun, Moon, LogOut } from 'lucide-react'

const BRAND = 'Nexa ERP'   // change the product name here

const MODULE_ICONS = {
  hr: Users, inventory: Package, sales: ShoppingCart,
  finance: Receipt, procurement: Truck, approvals: ClipboardCheck,
}

const ROLE_LABELS = { employee: 'Employee', hr: 'HR', manager: 'Manager', admin: 'Admin' }

function initials(name = '') {
  return name.split(' ').filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join('') || '?'
}

function Sidebar({ modules, features, active, onSelect, user, theme, onToggleTheme, onLogout }) {
  return (
    <aside className="sidebar glass">
      <div className="brand">
        <div className="brand-mark"><Sparkles size={18} /></div>
        <div className="brand-text">
          <div className="brand-name">{BRAND}</div>
          <div className="brand-sub">AI Assistant</div>
        </div>
      </div>

      <nav className="nav">
        <button className={`nav-item ${active === 'overview' ? 'active' : ''}`}
                onClick={() => onSelect('overview')} title="Overview">
          <LayoutDashboard size={18} /><span>Overview</span>
        </button>

        <div className="nav-label">Modules</div>
        {modules.map((m) => {
          const Icon = MODULE_ICONS[m.key] || LayoutDashboard
          return (
            <button key={m.key} className={`nav-item ${active === m.key ? 'active' : ''}`}
                    onClick={() => onSelect(m.key)} title={m.label}>
              <Icon size={18} /><span>{m.label}</span>
            </button>
          )
        })}

        {features?.analytics && (
          <>
            <div className="nav-label">Insights</div>
            <button className={`nav-item ${active === 'analytics' ? 'active' : ''}`}
                    onClick={() => onSelect('analytics')} title="Analytics">
              <BarChart3 size={18} /><span>Analytics</span>
            </button>
          </>
        )}
      </nav>

      <div className="sidebar-foot">
        <div className="user-card">
          <div className="avatar-circle">{initials(user.name)}</div>
          <div className="user-meta">
            <div className="user-name">{user.name}</div>
            <div className="user-role">{ROLE_LABELS[user.role] || user.role}</div>
          </div>
        </div>
        <div className="foot-actions">
          <button className="icon-btn" onClick={onToggleTheme}
                  title={theme === 'dark' ? 'Switch to light' : 'Switch to dark'}>
            {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
          </button>
          <button className="icon-btn" onClick={onLogout} title="Sign out">
            <LogOut size={17} />
          </button>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar