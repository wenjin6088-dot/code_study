import { beforeEach, describe, expect, it, vi } from 'vitest'

// practice-service (T126) does not exist yet — frontend/src/services/practice-service.ts
import { apiClient } from '@/services/api-client'
import { getTaskPractice } from '@/services/practice-service'

vi.mock('@/services/api-client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}))

const mockedGet = apiClient.get as unknown as ReturnType<typeof vi.fn>

describe('practice-service', () => {
  beforeEach(() => {
    mockedGet.mockReset()
  })

  describe('getTaskPractice', () => {
    it('should GET /tasks/{taskId}/practice and return the response data', async () => {
      const practiceResponse = {
        task_id: 'task-1',
        status: 'completed',
        problems: [
          {
            problem_number: 1,
            problem_type: 'follow_along',
            problem_statement: 'Type this code exactly.',
            learning_objective: 'Practice typing.',
            hints: ['Hint 1', 'Hint 2'],
            model_solution: 'print(1)',
            expected_output: '1',
          },
        ],
      }
      mockedGet.mockResolvedValueOnce({ data: practiceResponse })

      const result = await getTaskPractice('task-1')

      expect(mockedGet).toHaveBeenCalledWith('/tasks/task-1/practice')
      expect(result).toEqual(practiceResponse)
    })
  })
})
