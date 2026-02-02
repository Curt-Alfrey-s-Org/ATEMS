import axios from 'axios'

export const apiClient = axios.create({
  baseURL: '',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
  withCredentials: true,
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
