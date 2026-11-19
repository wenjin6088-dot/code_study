import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  withCredentials: true,
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.error?.message ?? error.message ?? '알 수 없는 오류가 발생했습니다'
    return Promise.reject(new Error(message))
  },
)
