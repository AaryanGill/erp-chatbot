import axios from 'axios'

// Vite's dev server proxy (see vite.config.js) forwards /api to Flask on :5000,
// so we don't hardcode the backend host.
const api = axios.create({
  baseURL: '/api',
})

// Attach the JWT token (if logged in) to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('erp_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// If the token is invalid or expired, log the user out
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const isAuthCall = error.config?.url?.startsWith('/auth/')
    if ((status === 401 || status === 422) && !isAuthCall) {
      localStorage.removeItem('erp_token')
      localStorage.removeItem('erp_user')
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

export const sendMessage = async (message) => {
  const response = await api.post('/chat/message', { message })
  return response.data // { reply, summary, table, module, intent, confidence }
}

export const getDashboard = async () => {
  const response = await api.get('/dashboard/summary')
  return response.data // { user, kpis, modules }
}

export const getAnalytics = async () => {
  const response = await api.get('/analytics/summary')
  return response.data // { totals, per_day, top_intents, modules, unanswered, recent }
}

export const login = async (username, password) => {
  const response = await api.post('/auth/login', { username, password })
  return response.data // { token, user }
}

export const register = async (username, email, password) => {
  const response = await api.post('/auth/register', { username, email, password })
  return response.data // { token, user }
}

export default api