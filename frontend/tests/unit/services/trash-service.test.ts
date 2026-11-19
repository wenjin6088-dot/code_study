import { beforeEach, describe, expect, it, vi } from 'vitest'

// trash-service.ts (T180, projects-only scope) does not exist yet —
// frontend/src/services/trash-service.ts.
//
// Expected contract (mirrors project-service.ts: thin wrappers around the
// shared `apiClient`; backend endpoints per backend/src/api/trash.py):
//
//   listTrash()                -> GET    /trash                               -> Project[] (unwraps { projects: [...] })
//   restoreProject(id)         -> POST   /trash/projects/{id}/restore          -> Project
//   permanentDeleteProject(id) -> DELETE /trash/projects/{id}/permanent-delete -> void
import * as trashService from '@/services/trash-service'
import { apiClient } from '@/services/api-client'

vi.mock('@/services/api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockedGet = apiClient.get as unknown as ReturnType<typeof vi.fn>
const mockedPost = apiClient.post as unknown as ReturnType<typeof vi.fn>
const mockedDelete = apiClient.delete as unknown as ReturnType<typeof vi.fn>

const mockTrashedProject = {
  id: 'project-1',
  title: 'Trashed Project',
  description: 'Was deleted',
  deletion_status: 'trashed',
}

describe('trash-service', () => {
  beforeEach(() => {
    mockedGet.mockReset()
    mockedPost.mockReset()
    mockedDelete.mockReset()
  })

  describe('listTrash', () => {
    it('should GET /trash and return the caller\'s trashed projects', async () => {
      mockedGet.mockResolvedValueOnce({ data: { projects: [mockTrashedProject] } })

      const result = await trashService.listTrash()

      expect(mockedGet).toHaveBeenCalledWith('/trash')
      expect(result).toEqual([mockTrashedProject])
    })

    it('should propagate the error when unauthenticated (401)', async () => {
      mockedGet.mockRejectedValueOnce(new Error('인증이 필요합니다'))

      await expect(trashService.listTrash()).rejects.toThrow('인증이 필요합니다')
    })
  })

  describe('restoreProject', () => {
    it('should POST /trash/projects/{id}/restore and return the restored project', async () => {
      const restored = { ...mockTrashedProject, deletion_status: 'active' }
      mockedPost.mockResolvedValueOnce({ data: restored })

      const result = await trashService.restoreProject('project-1')

      expect(mockedPost).toHaveBeenCalledWith('/trash/projects/project-1/restore')
      expect(result).toEqual(restored)
    })

    it('should propagate the error when the project is not found or not trashed (404)', async () => {
      mockedPost.mockRejectedValueOnce(new Error('프로젝트를 찾을 수 없습니다'))

      await expect(trashService.restoreProject('missing-id')).rejects.toThrow(
        '프로젝트를 찾을 수 없습니다',
      )
    })
  })

  describe('permanentDeleteProject', () => {
    it('should DELETE /trash/projects/{id}/permanent-delete', async () => {
      mockedDelete.mockResolvedValueOnce({ data: undefined })

      await trashService.permanentDeleteProject('project-1')

      expect(mockedDelete).toHaveBeenCalledWith('/trash/projects/project-1/permanent-delete')
    })

    it('should propagate the error when the project is not found or not trashed (404)', async () => {
      mockedDelete.mockRejectedValueOnce(new Error('프로젝트를 찾을 수 없습니다'))

      await expect(trashService.permanentDeleteProject('missing-id')).rejects.toThrow(
        '프로젝트를 찾을 수 없습니다',
      )
    })
  })
})
