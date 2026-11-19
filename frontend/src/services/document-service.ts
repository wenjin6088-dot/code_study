import { apiClient } from './api-client'

export type DocumentStatus = 'pending' | 'in_progress' | 'completed' | 'failed'

export interface DocumentConcept {
  name: string
  explanation: string
  analogy: string
  example: string
  use_cases: string
}

export interface DocumentChapter1 {
  title: string
  summary: string
}

export interface DocumentChapter2 {
  title: string
  concepts: DocumentConcept[]
}

export interface DocumentChapter3 {
  title: string
  flowchart: string
  file_breakdown: Record<string, string>
}

export interface DocumentExplanation {
  file: string
  line_start: number
  line_end: number
  code: string
  what_it_does: string
  syntax_breakdown: string
  analogy: string
  alternative_example: string
  notes: string
}

export interface DocumentChapter4 {
  title: string
  explanations: DocumentExplanation[]
}

export interface DocumentStep {
  step: number
  description: string
  data_state: string
}

export interface DocumentChapter5 {
  title: string
  steps: DocumentStep[]
}

export interface DocumentCoreConcept {
  name: string
  what_it_is: string
  why_used: string
  where_applied: string
}

export interface DocumentChapter6 {
  title: string
  concepts: DocumentCoreConcept[]
}

export interface DocumentMistake {
  wrong: string
  right: string
  why: string
  fix: string
}

export interface DocumentChapter7 {
  title: string
  mistakes: DocumentMistake[]
}

export interface DocumentContent {
  chapter1: DocumentChapter1
  chapter2: DocumentChapter2
  chapter3: DocumentChapter3
  chapter4: DocumentChapter4
  chapter5: DocumentChapter5
  chapter6: DocumentChapter6
  chapter7: DocumentChapter7
}

export interface TaskDocumentResponse {
  task_id: string
  status: DocumentStatus
  content: DocumentContent | null
  error: string | null
  generated_at: string | null
}

export interface TaskDocumentStatusResponse {
  status: DocumentStatus
  error: string | null
  estimated_seconds_remaining: number | null
}

export async function getTaskDocument(taskId: string): Promise<TaskDocumentResponse> {
  const response = await apiClient.get(`/tasks/${taskId}/document`)
  return response.data
}

export async function getTaskDocumentStatus(taskId: string): Promise<TaskDocumentStatusResponse> {
  const response = await apiClient.get(`/tasks/${taskId}/document/status`)
  return response.data
}
