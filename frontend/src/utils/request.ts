import axios from 'axios'
import type { InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'

// Create a custom axios instance
const request = axios.create({
  baseURL: '/api/v1',  // Proxy will route this to 8000
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request Interceptor
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Inject token to headers if exists
    const token = localStorage.getItem('token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response Interceptor
request.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    // Extract server detail or fallback to message
    const message = (error.response?.data as any)?.detail || error.message || 'Server Error'
    return Promise.reject(new Error(message))
  }
)

export default request
