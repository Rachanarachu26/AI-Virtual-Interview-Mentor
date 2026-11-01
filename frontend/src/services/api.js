import axios from 'axios'

// Base URL: dev uses Vite proxy ('/api'); override with VITE_API_URL in prod.
const baseURL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach the JWT to every request if present.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Global 401 handling -> log out.
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Helper to extract a friendly error message.
export function apiError(err, fallback = 'Something went wrong. Please try again.') {
  if (err?.response?.data?.detail) {
    const d = err.response.data.detail
    if (typeof d === 'string') return d
    if (Array.isArray(d) && d[0]?.msg) return d[0].msg
  }
  if (err?.message === 'Network Error') return 'Cannot reach the server. Is the backend running?'
  return fallback
}

// ---------------- Auth ----------------
export const authApi = {
  register: (data) => api.post('/api/auth/register', data),
  login: (data) => api.post('/api/auth/login', data),
  me: () => api.get('/api/auth/me'),
}

// ---------------- Resume ----------------
export const resumeApi = {
  upload: (formData) =>
    api.post('/api/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  latest: () => api.get('/api/resume/latest'),
  get: (id) => api.get(`/api/resume/${id}`),
}

// ---------------- Interviews ----------------
export const interviewApi = {
  meta: () => api.get('/api/interviews/meta/categories'),
  create: (data) => api.post('/api/interviews', data),
  get: (id) => api.get(`/api/interviews/${id}`),
  nextQuestion: (id) => api.post(`/api/interviews/${id}/question`),
  submitAnswer: (id, data) => api.post(`/api/interviews/${id}/answer`, data),
  results: (id) => api.get(`/api/interviews/${id}/results`),
  complete: (id) => api.post(`/api/interviews/${id}/complete`),
  history: () => api.get('/api/interviews/history'),
}

// ---------------- Speech ----------------
export const speechApi = {
  transcribe: (formData) =>
    api.post('/api/speech/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// ---------------- Vision ----------------
export const visionApi = {
  analyze: (frames) => api.post('/api/vision/analyze', { frames }),
}

export default api
