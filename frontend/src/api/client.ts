import axios from 'axios'
import type {
  AssessmentResult, AssistantResponse, DashboardSummary, ImprovementResult,
  KbCategory, KbDetail, KbSummary, MetaStatus, Participant, QrResult,
  QuizQuestion, ScamExample, ScamResult, Scenario, UrlResult, User, Workshop,
} from '@/types'

export const TOKEN_KEY = 'cybersathi.token'

/**
 * In dev, Vite proxies /api to the FastAPI backend on port 8000 (see vite.config.ts),
 * so no CORS configuration is needed. In a build, set VITE_API_BASE if the API lives
 * somewhere other than the same origin.
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? '',
  headers: { 'Content-Type': 'application/json' },
  timeout: 45000,
})

api.interceptors.request.use((config) => {
  try {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) config.headers.Authorization = `Bearer ${token}`
  } catch {
    // localStorage can throw in private mode — the public tools work anonymously anyway.
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      try {
        localStorage.removeItem(TOKEN_KEY)
      } catch { /* ignore */ }
    }
    return Promise.reject(error)
  },
)

const V1 = '/api/v1'

// ---------------------------------------------------------------- detection
export const analyzeScam = (text: string, channel = 'sms', language = 'auto') =>
  api.post<ScamResult>(`${V1}/scam/analyze`, { text, channel, language }).then((r) => r.data)

export const getScamExamples = (params?: { category?: string; language?: string }) =>
  api.get<ScamExample[]>(`${V1}/scam/examples`, { params }).then((r) => r.data)

export const checkUrl = (url: string) =>
  api.post<UrlResult>(`${V1}/url/check`, { url }).then((r) => r.data)

export const bulkCheckUrls = (urls: string[]) =>
  api.post<UrlResult[]>(`${V1}/url/bulk-check`, { urls }).then((r) => r.data)

export const analyzeQr = (payload: string) =>
  api.post<QrResult>(`${V1}/qr/analyze`, { payload }).then((r) => r.data)

export const getScenarios = () =>
  api.get<Scenario[]>(`${V1}/qr/scenarios`).then((r) => r.data)

// ---------------------------------------------------------- knowledge base
export const getArticles = (params?: { category?: string; q?: string }) =>
  api.get<KbSummary[]>(`${V1}/kb/articles`, { params }).then((r) => r.data)

export const getArticle = (slug: string) =>
  api.get<KbDetail>(`${V1}/kb/articles/${slug}`).then((r) => r.data)

export const getCategories = () =>
  api.get<KbCategory[]>(`${V1}/kb/categories`).then((r) => r.data)

// ---------------------------------------------------------------- assistant
export const askAssistant = (question: string, language = 'auto', simpleMode = false) =>
  api
    .post<AssistantResponse>(`${V1}/assistant/ask`, {
      question, language, simple_mode: simpleMode,
    })
    .then((r) => r.data)

export const sendAssistantFeedback = (logId: number, helpful: boolean) =>
  api.post(`${V1}/assistant/feedback`, { log_id: logId, helpful })

export const getSuggestions = (language: string) =>
  api.get<string[]>(`${V1}/assistant/suggestions`, { params: { language } }).then((r) => r.data)

// ---------------------------------------------------------------- community
export const getWorkshops = (params?: { district?: string }) =>
  api.get<Workshop[]>(`${V1}/workshops`, { params }).then((r) => r.data)

export const createWorkshop = (payload: Record<string, unknown>) =>
  api.post<Workshop>(`${V1}/workshops`, payload).then((r) => r.data)

export const getParticipants = (workshopId: number) =>
  api.get<Participant[]>(`${V1}/workshops/${workshopId}/participants`).then((r) => r.data)

export const addParticipants = (workshopId: number, participants: Record<string, unknown>[]) =>
  api.post<Participant[]>(`${V1}/workshops/${workshopId}/participants`, participants).then((r) => r.data)

export const getQuestions = (params: {
  workshop_id: number; participant_id: number
  type: 'pre' | 'post'; language: string; count?: number
}) => api.get<QuizQuestion[]>(`${V1}/assessment/questions`, { params }).then((r) => r.data)

export const submitAssessment = (payload: {
  participant_id: number; workshop_id: number
  type: 'pre' | 'post'
  answers: { question_id: number; selected_index: number }[]
  duration_seconds: number; language: string
}) => api.post<AssessmentResult>(`${V1}/assessment/submit`, payload).then((r) => r.data)

export const getImprovement = (participantId: number) =>
  api.get<ImprovementResult>(`${V1}/assessment/participant/${participantId}/improvement`).then((r) => r.data)

export const getDashboard = (params?: Record<string, string | undefined>) =>
  api.get<DashboardSummary>(`${V1}/dashboard/summary`, { params }).then((r) => r.data)

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

/** Export the impact data. `pdf` renders the printable report for the project appendix. */
export const exportUrl = (format: 'csv' | 'json' | 'pdf', district?: string) => {
  const params = new URLSearchParams({ format })
  if (district) params.set('district', district)
  return `${API_BASE}${V1}/dashboard/export?${params.toString()}`
}

/** Kept for existing callers. */
export const exportCsvUrl = () => exportUrl('csv')

export const createFeedback = (payload: {
  workshop_id: number
  participant_id?: number | null
  rating: number
  comment?: string | null
}) => api.post(`${V1}/feedback`, payload).then((r) => r.data)
export const certificateUrl = (participantId: number) =>
  `${import.meta.env.VITE_API_BASE ?? ''}${V1}/certificates/${participantId}`

// --------------------------------------------------------------------- auth
export const login = (email: string, password: string) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  return api
    .post<{ access_token: string; user: User }>(`${V1}/auth/login`, form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    .then((r) => r.data)
}

export const getMe = () => api.get<User>(`${V1}/auth/me`).then((r) => r.data)

// ------------------------------------------------------------------- admin
export const getUsers = () => api.get<User[]>(`${V1}/auth/users`).then((r) => r.data)

export const createStaffUser = (payload: {
  full_name: string; email: string; password: string; role: string
}) => api.post<User>(`${V1}/auth/users`, payload).then((r) => r.data)

export const setUserRole = (userId: number, role: string) =>
  api.patch<User>(`${V1}/auth/users/${userId}/role`, { role }).then((r) => r.data)

export const setUserActive = (userId: number, isActive: boolean) =>
  api.patch<User>(`${V1}/auth/users/${userId}/active`, { is_active: isActive }).then((r) => r.data)

// --------------------------------------------------------------------- meta
export const getStatus = () => api.get<MetaStatus>(`${V1}/meta/status`).then((r) => r.data)
export const getModelMetrics = () => api.get(`${V1}/meta/model-metrics`).then((r) => r.data)
export const getHelplines = () =>
  api.get<{ name_en: string; name_ta: string; value: string; type: string }[]>(`${V1}/meta/helplines`)
    .then((r) => r.data)

export default api
