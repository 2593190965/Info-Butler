import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

const token = localStorage.getItem('token')
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

api.interceptors.request.use((config) => {
  const t = localStorage.getItem('token')
  if (t) {
    config.headers['Authorization'] = `Bearer ${t}`
  } else {
    config.headers['X-API-Key'] = import.meta.env.VITE_API_KEY || 'dev-api-key-2026'
  }
  return config
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const msg = error.response?.data?.detail || error.message || '请求失败'

    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      delete api.defaults.headers.common['Authorization']
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else if (status === 404) {
      console.warn('Not Found:', msg)
    } else if (status >= 500) {
      console.error('Server Error:', msg)
    }

    return Promise.reject({ status, message: msg, data: null })
  }
)

export default api
