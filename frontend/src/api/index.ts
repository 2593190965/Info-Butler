import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  config.headers['X-API-Key'] = import.meta.env.VITE_API_KEY || 'dev-api-key-2026'
  return config
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const msg = error.response?.data?.message || error.message || '请求失败'

    if (status === 401) console.error('Unauthorized:', msg)
    else if (status === 404) console.warn('Not Found:', msg)
    else if (status >= 500) console.error('Server Error:', msg)

    return Promise.reject({ status, message: msg, data: null })
  }
)

export default api
