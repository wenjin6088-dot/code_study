import { apiClient } from './api-client'

export interface AuthUser {
  id: string
  email: string
  skillLevel: string
}

export async function register(email: string, password: string): Promise<AuthUser> {
  const response = await apiClient.post('/auth/register', { email, password })
  return response.data
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const response = await apiClient.post('/auth/login', { email, password })
  return response.data
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout')
}

export async function getCurrentUser(): Promise<AuthUser> {
  const response = await apiClient.get('/auth/me')
  return response.data
}

export async function refreshToken(): Promise<void> {
  await apiClient.post('/auth/refresh')
}
