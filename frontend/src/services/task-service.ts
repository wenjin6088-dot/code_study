import { apiClient } from './api-client'

export interface CodeFileInfo {
  file_name: string
  file_path: string | null
  file_extension: string | null
  file_size_bytes: number | null
}

export interface UploadedCodeInfo {
  detected_language: string | null
  complexity_level: string | null
  total_lines: number | null
  total_files: number | null
  upload_size_bytes: number | null
  files: CodeFileInfo[]
}

export interface Task {
  id: string
  project_id: string
  task_number: number
  title: string
  description: string | null
  upload_method: 'file' | 'folder' | 'paste' | null
  deletion_status: string
  created_at: string
  updated_at: string
  uploaded_code: UploadedCodeInfo | null
}

export interface CreateTaskFileInput {
  title: string
  description?: string
  uploadMethod: 'file' | 'folder'
  files: File[]
}

export interface CreateTaskPasteInput {
  title: string
  description?: string
  uploadMethod: 'paste'
  pasteContent: string
  pasteFilename: string
}

export type CreateTaskInput = CreateTaskFileInput | CreateTaskPasteInput

export interface UpdateTaskInput {
  title?: string
  description?: string
}

export interface TaskCodeFile {
  file_name: string
  file_path: string | null
  file_extension: string | null
  content: string
}

export interface TaskCodeResponse {
  files: TaskCodeFile[]
}

export async function listTasks(projectId: string): Promise<Task[]> {
  const response = await apiClient.get(`/projects/${projectId}/tasks`)
  return response.data
}

export async function getTask(taskId: string): Promise<Task> {
  const response = await apiClient.get(`/tasks/${taskId}`)
  return response.data
}

export async function createTask(projectId: string, input: CreateTaskInput): Promise<Task> {
  const formData = new FormData()
  formData.append('title', input.title)
  if (input.description) {
    formData.append('description', input.description)
  }
  formData.append('upload_method', input.uploadMethod)

  if (input.uploadMethod === 'paste') {
    formData.append('paste_content', input.pasteContent)
    formData.append('paste_filename', input.pasteFilename)
  } else {
    for (const file of input.files) {
      formData.append('files', file, file.webkitRelativePath || file.name)
    }
  }

  const response = await apiClient.post(`/projects/${projectId}/tasks`, formData)
  return response.data
}

export async function updateTask(taskId: string, input: UpdateTaskInput): Promise<Task> {
  const response = await apiClient.patch(`/tasks/${taskId}`, input)
  return response.data
}

export async function removeTask(taskId: string): Promise<void> {
  await apiClient.delete(`/tasks/${taskId}`)
}

export async function getTaskCode(taskId: string): Promise<TaskCodeResponse> {
  const response = await apiClient.get(`/tasks/${taskId}/code`)
  return response.data
}
