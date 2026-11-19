import { useState } from 'react'
import { Sparkles } from 'lucide-react'
import { login, register } from '../services/api'

const BRAND = 'Nexa ERP'   // change the product name here

function Login({ onLoginSuccess }) {
  const [mode, setMode] = useState('login') // 'login' or 'register'
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = mode === 'login'
        ? await login(username, password)
        : await register(username, email, password)
      localStorage.setItem('erp_token', data.token)
      localStorage.setItem('erp_user', JSON.stringify(data.user))
      onLoginSuccess(data.user)
    } catch (err) {
      setError(err.response?.data?.error ||
        (mode === 'login' ? 'Invalid username or password.' : 'Registration failed.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-screen">
      <form className="auth-card glass" onSubmit={handleSubmit}>
        <div className="auth-brand">
          <div className="brand-mark"><Sparkles size={18} /></div>
          <span>{BRAND}</span>
        </div>

        <h1>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h1>
        <p className="auth-sub">
          {mode === 'login' ? 'Sign in to continue to your ERP assistant.' : 'Register to start using the assistant.'}
        </p>

        <label className="field">
          <span>Username</span>
          <input type="text" value={username} onChange={(e) => setUsername(e.target.value)}
                 autoComplete="username" required autoFocus />
        </label>

        {mode === 'register' && (
          <label className="field">
            <span>Email</span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
        )}

        <label className="field">
          <span>Password</span>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                 autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required />
        </label>

        {error && <div className="auth-error">{error}</div>}

        <button type="submit" className="btn primary block" disabled={loading}>
          {loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
        </button>

        <button type="button" className="auth-switch"
                onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>
          {mode === 'login' ? "Don't have an account? Register" : 'Already have an account? Sign in'}
        </button>
      </form>
    </div>
  )
}

export default Login