import { apiClient } from './api-client'
import type { Project } from './project-service'

export async function listTrash(): Promise<Project[]> {
  const response = await apiClient.get('/trash')
  return response.data.projects
}

export async function restoreProject(id: string): Promise<Project> {
  const response = await apiClient.post(`/trash/projects/${id}/restore`)
  return response.data
}

export async function permanentDeleteProject(id: string): Promise<void> {
  await apiClient.delete(`/trash/projects/${id}/permanent-delete`)
}
