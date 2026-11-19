import { beforeEach, describe, expect, it, vi } from 'vitest'

// project-service.ts (T053) does not exist yet — this import will fail until
// it is created at frontend/src/services/project-service.ts.
//
// Expected contract (mirrors frontend/src/services/auth-service.ts: thin
// wrappers around the shared `apiClient`, snake_case fields from the backend
// per backend/src/api/projects.py T043-T050, errors propagate as-is because
// apiClient's response interceptor already normalizes them to Error(message)):
//
//   export interface Project {
//     id: string
//     title: string
//     description: string | null
//     created_at: string
//     updated_at: string
//     last_activity_at: string
//   }
//
//   listProjects()                          -> GET    /projects            -> Project[]
//   getProject(id)                          -> GET    /projects/{id}       -> Project
//   createProject({ title, description? })  -> POST   /projects            -> Project
//   updateProject(id, { title?, description? }) -> PATCH /projects/{id}    -> Project
//   removeProject(id)                       -> DELETE /projects/{id}       -> void
//
// Naming note: "removeProject" (not "deleteProject") mirrors the task
// description's own wording ("remove (delete) projects") and avoids shadowing
// the `delete` keyword, matching the getCurrentUser-style verb+Noun pattern
// already used in auth-service.ts.
import * as projectService from '@/services/project-service'
import { apiClient } from '@/services/api-client'

vi.mock('@/services/api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockedGet = apiClient.get as unknown as ReturnType<typeof vi.fn>
const mockedPost = apiClient.post as unknown as ReturnType<typeof vi.fn>
const mockedPatch = apiClient.patch as unknown as ReturnType<typeof vi.fn>
const mockedDelete = apiClient.delete as unknown as ReturnType<typeof vi.fn>

const mockProject = {
  id: 'project-1',
  title: 'My First Project',
  description: 'Learning FastAPI',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  last_activity_at: '2026-01-02T00:00:00Z',
}

describe('project-service', () => {
  beforeEach(() => {
    mockedGet.mockReset()
    mockedPost.mockReset()
    mockedPatch.mockReset()
    mockedDelete.mockReset()
  })

  describe('listProjects', () => {
    it('should GET /projects and return the list of the current user\'s projects', async () => {
      mockedGet.mockResolvedValueOnce({ data: [mockProject] })

      const result = await projectService.listProjects()

      expect(mockedGet).toHaveBeenCalledWith('/projects')
      expect(result).toEqual([mockProject])
    })

    it('should propagate the error when unauthenticated (401)', async () => {
      mockedGet.mockRejectedValueOnce(new Error('인증이 필요합니다'))

      await expect(projectService.listProjects()).rejects.toThrow('인증이 필요합니다')
    })
  })

  describe('getProject', () => {
    it('should GET /projects/{id} and return the project', async () => {
      mockedGet.mockResolvedValueOnce({ data: mockProject })

      const result = await projectService.getProject('project-1')

      expect(mockedGet).toHaveBeenCalledWith('/projects/project-1')
      expect(result).toEqual(mockProject)
    })

    it('should propagate the error when the project is not found or not owned (404)', async () => {
      mockedGet.mockRejectedValueOnce(new Error('프로젝트를 찾을 수 없습니다'))

      await expect(projectService.getProject('missing-id')).rejects.toThrow(
        '프로젝트를 찾을 수 없습니다',
      )
    })
  })

  describe('createProject', () => {
    it('should POST /projects with title and description and return the created project', async () => {
      mockedPost.mockResolvedValueOnce({ data: mockProject })

      const result = await projectService.createProject({
        title: 'My First Project',
        description: 'Learning FastAPI',
      })

      expect(mockedPost).toHaveBeenCalledWith('/projects', {
        title: 'My First Project',
        description: 'Learning FastAPI',
      })
      expect(result).toEqual(mockProject)
    })

    it('should POST /projects with only a title when description is omitted', async () => {
      mockedPost.mockResolvedValueOnce({ data: mockProject })

      await projectService.createProject({ title: 'My First Project' })

      expect(mockedPost).toHaveBeenCalledWith('/projects', { title: 'My First Project' })
    })

    it('should propagate the error on validation failure (e.g. empty title, 400)', async () => {
      mockedPost.mockRejectedValueOnce(new Error('제목을 입력해 주세요'))

      await expect(projectService.createProject({ title: '' })).rejects.toThrow(
        '제목을 입력해 주세요',
      )
    })
  })

  describe('updateProject', () => {
    it('should PATCH /projects/{id} with the changed fields and return the updated project', async () => {
      const updated = { ...mockProject, title: 'Renamed Project' }
      mockedPatch.mockResolvedValueOnce({ data: updated })

      const result = await projectService.updateProject('project-1', { title: 'Renamed Project' })

      expect(mockedPatch).toHaveBeenCalledWith('/projects/project-1', { title: 'Renamed Project' })
      expect(result).toEqual(updated)
    })

    it('should propagate the error when the project is not found or not owned (404)', async () => {
      mockedPatch.mockRejectedValueOnce(new Error('프로젝트를 찾을 수 없습니다'))

      await expect(
        projectService.updateProject('missing-id', { title: 'X' }),
      ).rejects.toThrow('프로젝트를 찾을 수 없습니다')
    })
  })

  describe('removeProject', () => {
    it('should DELETE /projects/{id} (soft delete / move to trash)', async () => {
      mockedDelete.mockResolvedValueOnce({ data: undefined })

      await projectService.removeProject('project-1')

      expect(mockedDelete).toHaveBeenCalledWith('/projects/project-1')
    })

    it('should propagate the error when the project is not found or not owned (404)', async () => {
      mockedDelete.mockRejectedValueOnce(new Error('프로젝트를 찾을 수 없습니다'))

      await expect(projectService.removeProject('missing-id')).rejects.toThrow(
        '프로젝트를 찾을 수 없습니다',
      )
    })
  })
})
