import { useState, useEffect, useCallback, useMemo } from 'react'
import Login from './components/Login'
import Sidebar from './components/Sidebar'
import KpiCards from './components/KpiCards'
import ChatPanel from './components/ChatPanel'
import Analytics from './components/Analytics'
import { getDashboard } from './services/api'
import { useChat } from './hooks/useChat'

function greeting() {
  const h = new Date().getHours()
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'
}

function useTheme() {
  const [theme, setTheme] = useState(() =>
    localStorage.getItem('erp_theme') ||
    (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('erp_theme', theme)
  }, [theme])

  return [theme, () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))]
}

function Shell({ onLogout }) {
  const [theme, toggleTheme] = useTheme()
  const [dash, setDash] = useState(null)
  const [active, setActive] = useState('overview')

  const refresh = useCallback(() => {
    getDashboard().then(setDash).catch(() => {})
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const { messages, loading, send, clear } = useChat(refresh)

  const modules = dash?.modules ?? []
  const user = dash?.user ?? JSON.parse(localStorage.getItem('erp_user') || '{}')
  const firstName = (user.name || user.username || '').split(' ')[0]

  // Buttons under the chat: the chosen module's actions, or one per module on Overview
  const actions = useMemo(() => {
    if (active !== 'overview') return modules.find((m) => m.key === active)?.actions ?? []
    return modules.flatMap((m) => m.actions.slice(0, 1)).slice(0, 6)
  }, [active, modules])

  const starters = useMemo(
    () => {
      const list = modules.flatMap((m) => m.actions.slice(0, 2)).slice(0, 6)
      return list.length % 2 ? list.slice(0, -1) : list      // keep the grid in even rows
    }, [modules])

  const activeLabel = active === 'overview' ? 'Overview' : modules.find((m) => m.key === active)?.label
  const contextLabel = active === 'overview' ? 'Online · all your modules' : `Online · ${activeLabel} module`

  return (
    <div className="app">
      <Sidebar modules={modules} features={dash?.features} active={active} onSelect={setActive}
               user={{ name: user.name || user.username || '', role: user.role || '' }}
               theme={theme} onToggleTheme={toggleTheme} onLogout={onLogout} />

      <main className="main">
        {active === 'analytics' ? (
          <Analytics />
        ) : (
          <>
            <header className="page-head">
              <h1>{greeting()}, {firstName}</h1>
              <p>{active === 'overview'
                ? 'Here is where things stand today.'
                : `${activeLabel} — pick an action below or type your own question.`}</p>
            </header>

            <KpiCards kpis={dash?.kpis ?? []} loading={!dash} onPick={send} />

            <ChatPanel messages={messages} loading={loading} onSend={send} onClear={clear}
                       actions={actions} starters={starters} contextLabel={contextLabel} />
          </>
        )}
      </main>
    </div>
  )
}

function App() {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('erp_user')) } catch { return null }
  })
  const hasToken = !!localStorage.getItem('erp_token')

  const handleLogout = () => {
    localStorage.removeItem('erp_token')
    localStorage.removeItem('erp_user')
    setUser(null)
  }

  // Keep the theme applied on the login screen too
  useTheme()

  if (!user || !hasToken) return <Login onLoginSuccess={setUser} />
  return <Shell onLogout={handleLogout} />
}

export default App