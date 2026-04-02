import axios from 'axios'

function newRequestId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 12)}`
}

const apiClient = axios.create({
  baseURL: '',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
  withCredentials: true,
})

apiClient.interceptors.request.use((config) => {
  const headers = config.headers ?? {}
  if (!headers['X-Request-ID']) {
    headers['X-Request-ID'] = newRequestId()
  }
  config.headers = headers
  return config
})

apiClient.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname)
    }
    return Promise.reject(err)
  }
)

export default apiClient
