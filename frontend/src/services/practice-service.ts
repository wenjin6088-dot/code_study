import { apiClient } from './api-client'

export type PracticeProblemType = 'follow_along' | 'fill_blanks' | 'modify' | 'debug' | 'create'
export type PracticeStatus = 'pending' | 'completed'

export interface PracticeProblem {
  problem_number: number
  problem_type: PracticeProblemType
  problem_statement: string
  learning_objective: string | null
  hints: string[] | null
  model_solution: string | null
  expected_output: string | null
}

export interface TaskPracticeResponse {
  task_id: string
  status: PracticeStatus
  problems: PracticeProblem[]
}

export async function getTaskPractice(taskId: string): Promise<TaskPracticeResponse> {
  const response = await apiClient.get(`/tasks/${taskId}/practice`)
  return response.data
}
