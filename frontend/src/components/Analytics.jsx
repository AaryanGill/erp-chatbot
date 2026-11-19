import { useEffect, useState, useCallback } from 'react'
import { RefreshCw } from 'lucide-react'
import { getAnalytics } from '../services/api'

function Stat({ label, value, hint }) {
  return (
    <div className="kpi glass">
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{value}</span>
      <span className="kpi-hint">{hint}</span>
    </div>
  )
}

// Vertical bars: one per day
function DayChart({ data }) {
  const max = Math.max(1, ...data.map((d) => d.count))
  return (
    <div className="daychart">
      {data.map((d) => (
        <div className="daycol" key={d.date} title={`${d.label}: ${d.count} question(s)`}>
          <span className="daycount">{d.count || ''}</span>
          <div className="daybar-track">
            <div className="daybar" style={{ height: `${(d.count / max) * 100}%` }} />
          </div>
          <span className="daylabel">{d.label.slice(0, 2)}</span>
        </div>
      ))}
    </div>
  )
}

// Horizontal bars with a label and a number
function HBars({ items, empty = 'No data yet.' }) {
  if (!items.length) return <p className="muted">{empty}</p>
  const max = Math.max(1, ...items.map((i) => i.count))
  return (
    <div className="hbars">
      {items.map((i) => (
        <div className="hbar" key={i.label}>
          <div className="hbar-top"><span>{i.label}</span><span className="hbar-n">{i.count}</span></div>
          <div className="hbar-track"><div className="hbar-fill" style={{ width: `${(i.count / max) * 100}%` }} /></div>
        </div>
      ))}
    </div>
  )
}

function Analytics() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    setError('')
    getAnalytics().then(setData).catch(() => setError('Could not load analytics.'))
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <div className="analytics">
      <header className="page-head row">
        <div>
          <h1>Analytics</h1>
          <p>How people are using the assistant over the last 14 days.</p>
        </div>
        <button className="ghost-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
      </header>

      {error && <div className="auth-error">{error}</div>}
      {!data && !error && <div className="kpis">{[0, 1, 2, 3].map((i) => <div key={i} className="kpi glass skeleton" />)}</div>}

      {data && (
        <>
          <section className="kpis">
            <Stat label="Questions asked" value={data.totals.questions} hint="All time" />
            <Stat label="Today" value={data.totals.today} hint="Questions so far" />
            <Stat label="Active users" value={data.totals.active_users} hint="Have used the assistant" />
            <Stat label="Understood" value={`${data.totals.answered_pct}%`} hint="Answered with a real result" />
            <Stat label="Blocked" value={data.totals.blocked} hint="Stopped by access control" />
          </section>

          <section className="panels two">
            <div className="panel glass">
              <h3>Questions per day</h3>
              <DayChart data={data.per_day} />
            </div>
            <div className="panel glass">
              <h3>Usage by module</h3>
              <HBars items={data.modules} />
            </div>
          </section>

          <section className="panels two">
            <div className="panel glass">
              <h3>Most asked</h3>
              <HBars items={data.top_intents} />
            </div>
            <div className="panel glass">
              <h3>Not understood</h3>
              {data.unanswered.length === 0
                ? <p className="muted">Every question was understood.</p>
                : <ul className="plain-list">
                    {data.unanswered.map((u, i) => (
                      <li key={i}><span>{u.query}</span><span className="muted">{u.time}</span></li>
                    ))}
                  </ul>}
              <p className="panel-note">Add questions like these to <code>training_data.py</code> to make the assistant smarter.</p>
            </div>
          </section>

          <section className="panel glass">
            <h3>Recent activity</h3>
            <div className="table-wrap">
              <table className="data-table">
                <thead><tr><th>When</th><th>User</th><th>Question</th><th>Topic</th></tr></thead>
                <tbody>
                  {data.recent.map((r, i) => (
                    <tr key={i}>
                      <td className="first">{r.time}</td><td>{r.user}</td><td>{r.query}</td>
                      <td><span className="badge neutral">{r.topic}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  )
}

export default Analytics