import { beforeEach, describe, expect, it, vi } from 'vitest'

// task-service (T080) does not exist yet — frontend/src/services/task-service.ts
//
// Mirrors project-service.ts's pattern: thin axios wrapper functions around
// apiClient, reusing the shared apiClient (same baseURL '/api/v1',
// withCredentials, error-message interceptor already covered by
// api-client.ts's own tests, if any exist — this file only tests that
// task-service calls the right endpoints with the right payload shape).
import { apiClient } from '@/services/api-client'
import {
  createTask,
  getTask,
  getTaskCode,
  listTasks,
  removeTask,
  updateTask,
} from '@/services/task-service'

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

const task1 = {
  id: 'task-1',
  project_id: 'project-1',
  task_number: 1,
  title: 'My First Task',
  description: null,
  upload_method: 'file',
  deletion_status: 'active',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  uploaded_code: null,
}

describe('task-service', () => {
  beforeEach(() => {
    mockedGet.mockReset()
    mockedPost.mockReset()
    mockedPatch.mockReset()
    mockedDelete.mockReset()
  })

  describe('listTasks', () => {
    it('should GET /projects/{projectId}/tasks', async () => {
      mockedGet.mockResolvedValueOnce({ data: [task1] })

      const result = await listTasks('project-1')

      expect(mockedGet).toHaveBeenCalledWith('/projects/project-1/tasks')
      expect(result).toEqual([task1])
    })
  })

  describe('getTask', () => {
    it('should GET /tasks/{taskId}', async () => {
      mockedGet.mockResolvedValueOnce({ data: task1 })

      const result = await getTask('task-1')

      expect(mockedGet).toHaveBeenCalledWith('/tasks/task-1')
      expect(result).toEqual(task1)
    })
  })

  describe('updateTask', () => {
    it('should PATCH /tasks/{taskId} with the given fields', async () => {
      mockedPatch.mockResolvedValueOnce({ data: task1 })

      const result = await updateTask('task-1', { title: 'Updated' })

      expect(mockedPatch).toHaveBeenCalledWith('/tasks/task-1', { title: 'Updated' })
      expect(result).toEqual(task1)
    })
  })

  describe('removeTask', () => {
    it('should DELETE /tasks/{taskId}', async () => {
      mockedDelete.mockResolvedValueOnce({ data: undefined })

      await removeTask('task-1')

      expect(mockedDelete).toHaveBeenCalledWith('/tasks/task-1')
    })
  })

  describe('getTaskCode', () => {
    it('should GET /tasks/{taskId}/code', async () => {
      const codeResponse = {
        files: [{ file_name: 'main.py', file_path: null, file_extension: '.py', content: 'x=1' }],
      }
      mockedGet.mockResolvedValueOnce({ data: codeResponse })

      const result = await getTaskCode('task-1')

      expect(mockedGet).toHaveBeenCalledWith('/tasks/task-1/code')
      expect(result).toEqual(codeResponse)
    })
  })

  describe('createTask', () => {
    it('should POST FormData to /projects/{projectId}/tasks for a file upload, with snake_case field names', async () => {
      mockedPost.mockResolvedValueOnce({ data: task1 })

      const file1 = new File(['print(1)'], 'main.py', { type: 'text/plain' })

      const result = await createTask('project-1', {
        title: 'My First Task',
        description: 'desc',
        uploadMethod: 'file',
        files: [file1],
      })

      expect(mockedPost).toHaveBeenCalledTimes(1)
      const [url, formData] = mockedPost.mock.calls[0]
      expect(url).toBe('/projects/project-1/tasks')
      expect(formData).toBeInstanceOf(FormData)
      expect(formData.get('title')).toBe('My First Task')
      expect(formData.get('description')).toBe('desc')
      expect(formData.get('upload_method')).toBe('file')
      const files = formData.getAll('files')
      expect(files).toHaveLength(1)
      expect((files[0] as File).name).toBe('main.py')
      expect(result).toEqual(task1)
    })

    it('should omit description from FormData when not provided', async () => {
      mockedPost.mockResolvedValueOnce({ data: task1 })

      const file1 = new File(['print(1)'], 'main.py', { type: 'text/plain' })

      await createTask('project-1', {
        title: 'My First Task',
        uploadMethod: 'file',
        files: [file1],
      })

      const [, formData] = mockedPost.mock.calls[0]
      expect(formData.has('description')).toBe(false)
    })

    it('should append each file under the "files" field, using webkitRelativePath as filename for folder uploads', async () => {
      mockedPost.mockResolvedValueOnce({ data: task1 })

      const file1 = new File(['a'], 'a.py', { type: 'text/plain' })
      Object.defineProperty(file1, 'webkitRelativePath', { value: 'myfolder/a.py' })
      const file2 = new File(['b'], 'b.py', { type: 'text/plain' })
      Object.defineProperty(file2, 'webkitRelativePath', { value: 'myfolder/sub/b.py' })

      await createTask('project-1', {
        title: 'My First Task',
        uploadMethod: 'folder',
        files: [file1, file2],
      })

      const [, formData] = mockedPost.mock.calls[0]
      expect(formData.get('upload_method')).toBe('folder')
      const files = formData.getAll('files') as File[]
      expect(files).toHaveLength(2)
      expect(files[0].name).toBe('myfolder/a.py')
      expect(files[1].name).toBe('myfolder/sub/b.py')
    })

    it('should POST paste_content/paste_filename for a paste upload', async () => {
      mockedPost.mockResolvedValueOnce({ data: task1 })

      await createTask('project-1', {
        title: 'My First Task',
        uploadMethod: 'paste',
        pasteContent: 'print(1)',
        pasteFilename: 'pasted.py',
      })

      const [url, formData] = mockedPost.mock.calls[0]
      expect(url).toBe('/projects/project-1/tasks')
      expect(formData.get('upload_method')).toBe('paste')
      expect(formData.get('paste_content')).toBe('print(1)')
      expect(formData.get('paste_filename')).toBe('pasted.py')
      expect(formData.has('files')).toBe(false)
    })
  })
})
