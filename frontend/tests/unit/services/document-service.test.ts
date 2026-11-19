import { beforeEach, describe, expect, it, vi } from 'vitest'

// document-service (T106) does not exist yet — frontend/src/services/document-service.ts
//
// Mirrors task-service.ts's pattern: thin axios wrapper functions around the
// shared apiClient. This file only tests that document-service calls the
// right endpoints and returns the response payload as-is.
import { apiClient } from '@/services/api-client'
import { getTaskDocument, getTaskDocumentStatus } from '@/services/document-service'

vi.mock('@/services/api-client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}))

const mockedGet = apiClient.get as unknown as ReturnType<typeof vi.fn>

describe('document-service', () => {
  beforeEach(() => {
    mockedGet.mockReset()
  })

  describe('getTaskDocument', () => {
    it('should GET /tasks/{taskId}/document and return the response data', async () => {
      const documentResponse = {
        task_id: 'task-1',
        status: 'completed',
        content: { chapter1: { title: 'What This Code Does', summary: 'It adds numbers.' } },
        error: null,
        generated_at: '2026-01-01T00:00:00Z',
      }
      mockedGet.mockResolvedValueOnce({ data: documentResponse })

      const result = await getTaskDocument('task-1')

      expect(mockedGet).toHaveBeenCalledWith('/tasks/task-1/document')
      expect(result).toEqual(documentResponse)
    })
  })

  describe('getTaskDocumentStatus', () => {
    it('should GET /tasks/{taskId}/document/status and return the response data', async () => {
      const statusResponse = {
        status: 'in_progress',
        error: null,
        estimated_seconds_remaining: 42,
      }
      mockedGet.mockResolvedValueOnce({ data: statusResponse })

      const result = await getTaskDocumentStatus('task-1')

      expect(mockedGet).toHaveBeenCalledWith('/tasks/task-1/document/status')
      expect(result).toEqual(statusResponse)
    })
  })
})
