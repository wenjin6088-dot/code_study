import { apiClient } from './api-client'

export interface Project {
  id: string
  title: string
  description: string | null
  created_at: string
  updated_at: string
  last_activity_at: string
}

export interface CreateProjectInput {
  title: string
  description?: string
}

export interface UpdateProjectInput {
  title?: string
  description?: string
}

export async function listProjects(): Promise<Project[]> {
  const response = await apiClient.get('/projects')
  return response.data
}

export async function getProject(id: string): Promise<Project> {
  const response = await apiClient.get(`/projects/${id}`)
  return response.data
}

export async function createProject(input: CreateProjectInput): Promise<Project> {
  const response = await apiClient.post('/projects', input)
  return response.data
}

export async function updateProject(id: string, input: UpdateProjectInput): Promise<Project> {
  const response = await apiClient.patch(`/projects/${id}`, input)
  return response.data
}

export async function removeProject(id: string): Promise<void> {
  await apiClient.delete(`/projects/${id}`)
}
