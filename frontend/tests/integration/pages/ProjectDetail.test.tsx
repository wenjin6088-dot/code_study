import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// ProjectDetail page (T055) does not exist yet — frontend/src/pages/ProjectDetail.tsx.
// It replaces the inline placeholder `function ProjectDetail()` currently
// defined in frontend/src/App.tsx (that swap is GREEN-phase work; this test
// renders the page component directly, reading :projectId off the route via
// react-router-dom's useParams, so it must be rendered under a <Route
// path="/projects/:projectId">).
//
// Expected contract:
//   - Reads `projectId` from the route params and fetches that project via
//     @/services/project-service#getProject(projectId), using TanStack Query
//     (useQuery({ queryKey: ['project', projectId], queryFn: ... })) — same
//     QueryClientProvider-wrapping requirement as Dashboard; see
//     frontend/tests/test-utils/queryClient.ts.
//   - Loading state: a `role="status"` element while the query is pending.
//   - Success: renders the project's title (heading) and description.
//   - A "Tasks" section (heading text "Tasks") is always rendered below the
//     project info as an intentional skeleton/placeholder — Task entities
//     don't exist yet per tasks.md T055 — containing an empty-state message
//     (any text is acceptable; this test only asserts the "Tasks" heading
//     and that no task items are rendered).
//   - Error/not-found: when getProject rejects (404 not found/not owned),
//     shows a message containing "찾을 수 없습니다" instead of crashing.
import { fireEvent, waitFor } from '@testing-library/react'

import ProjectDetail from '@/pages/ProjectDetail'
import * as projectService from '@/services/project-service'
import * as taskService from '@/services/task-service'
import { createTestQueryClient } from '../../test-utils/queryClient'

vi.mock('@/services/project-service')
// T082: task-service is mocked too, so ProjectDetail's task list/creation
// slice can be tested deterministically without hitting the real apiClient.
// listTasks defaults to resolving an empty array in beforeEach below so the
// pre-existing "Tasks placeholder" test (which only cares about getProject)
// keeps seeing "no tasks" deterministically instead of relying on an
// unmocked network call.
vi.mock('@/services/task-service')

const mockedGetProject = projectService.getProject as unknown as ReturnType<typeof vi.fn>
const mockedUpdateProject = projectService.updateProject as unknown as ReturnType<typeof vi.fn>
const mockedRemoveProject = projectService.removeProject as unknown as ReturnType<typeof vi.fn>
const mockedListTasks = taskService.listTasks as unknown as ReturnType<typeof vi.fn>
const mockedCreateTask = taskService.createTask as unknown as ReturnType<typeof vi.fn>

const project1 = {
  id: 'project-1',
  title: 'My First Project',
  description: 'Learning FastAPI',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  last_activity_at: '2026-01-02T00:00:00Z',
}

const task1 = {
  id: 'task-1',
  project_id: 'project-1',
  task_number: 1,
  title: 'My First Task',
  description: 'A simple task',
  upload_method: 'file' as const,
  deletion_status: 'active',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  uploaded_code: null,
}

function renderProjectDetail(projectId = 'project-1') {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/projects/${projectId}`]}>
        <Routes>
          <Route path="/projects/:projectId" element={<ProjectDetail />} />
          <Route
            path="/projects/:projectId/tasks/:taskId"
            element={<div>Task Detail Page</div>}
          />
          <Route path="/" element={<div>Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProjectDetail page', () => {
  beforeEach(() => {
    mockedGetProject.mockReset()
    mockedUpdateProject.mockReset()
    mockedRemoveProject.mockReset()
    mockedListTasks.mockReset()
    mockedCreateTask.mockReset()
    mockedListTasks.mockResolvedValue([])
  })

  it('should show a loading state while the project is being fetched', () => {
    mockedGetProject.mockReturnValue(new Promise(() => {}))

    renderProjectDetail('project-1')

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('should fetch the project matching the :projectId route param', async () => {
    mockedGetProject.mockResolvedValueOnce(project1)

    renderProjectDetail('project-1')

    await screen.findByText('My First Project')
    expect(mockedGetProject).toHaveBeenCalledWith('project-1')
  })

  it('should render the project title and description once loaded', async () => {
    mockedGetProject.mockResolvedValueOnce(project1)

    renderProjectDetail('project-1')

    expect(await screen.findByText('My First Project')).toBeInTheDocument()
    expect(screen.getByText('Learning FastAPI')).toBeInTheDocument()
  })

  it('should render a "Tasks" placeholder section', async () => {
    mockedGetProject.mockResolvedValueOnce(project1)

    renderProjectDetail('project-1')

    await screen.findByText('My First Project')
    expect(screen.getByRole('heading', { name: /tasks/i })).toBeInTheDocument()
    expect(screen.queryByRole('listitem')).not.toBeInTheDocument()
  })

  it('should show a not-found message when the project cannot be fetched (404)', async () => {
    mockedGetProject.mockRejectedValueOnce(new Error('프로젝트를 찾을 수 없습니다'))

    renderProjectDetail('missing-id')

    expect(await screen.findByText(/찾을 수 없습니다/)).toBeInTheDocument()
  })

  // T056a: Edit project title/description.
  // Calls updateProject() (already implemented, backend PATCH already GREEN
  // since T049) directly from this page, mirroring how CreateProjectModal
  // calls createProject() itself rather than delegating to a parent.
  describe('editing the project', () => {
    function fillEditTitle(value: string) {
      fireEvent.change(screen.getByLabelText(/^title$/i), { target: { value } })
    }

    it('should render an Edit button once the project has loaded', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)

      renderProjectDetail('project-1')

      expect(await screen.findByRole('button', { name: /edit/i })).toBeInTheDocument()
    })

    it('should enter edit mode with Title/Description pre-filled when Edit is clicked', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)

      renderProjectDetail('project-1')

      fireEvent.click(await screen.findByRole('button', { name: /edit/i }))

      expect(screen.getByLabelText(/^title$/i)).toHaveValue('My First Project')
      expect(screen.getByLabelText(/^description$/i)).toHaveValue('Learning FastAPI')
      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
    })

    it('should disable Save while the title is empty or whitespace-only', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)

      renderProjectDetail('project-1')

      fireEvent.click(await screen.findByRole('button', { name: /edit/i }))
      fillEditTitle('   ')

      expect(screen.getByRole('button', { name: /save/i })).toBeDisabled()
    })

    it('should discard changes and exit edit mode when Cancel is clicked, without calling updateProject', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)

      renderProjectDetail('project-1')

      fireEvent.click(await screen.findByRole('button', { name: /edit/i }))
      fillEditTitle('Changed but discarded')
      fireEvent.click(screen.getByRole('button', { name: /cancel/i }))

      expect(mockedUpdateProject).not.toHaveBeenCalled()
      expect(screen.queryByLabelText(/^title$/i)).not.toBeInTheDocument()
      expect(screen.getByText('My First Project')).toBeInTheDocument()
    })

    it('should call updateProject with the edited title/description on Save', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)
      mockedUpdateProject.mockResolvedValueOnce({
        ...project1,
        title: 'Updated Title',
        description: 'Updated description',
      })

      renderProjectDetail('project-1')

      fireEvent.click(await screen.findByRole('button', { name: /edit/i }))
      fillEditTitle('Updated Title')
      fireEvent.change(screen.getByLabelText(/^description$/i), {
        target: { value: 'Updated description' },
      })
      fireEvent.click(screen.getByRole('button', { name: /save/i }))

      await waitFor(() =>
        expect(mockedUpdateProject).toHaveBeenCalledWith('project-1', {
          title: 'Updated Title',
          description: 'Updated description',
        }),
      )
    })

    it('should exit edit mode and display the updated title/description after a successful save', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)
      mockedUpdateProject.mockResolvedValueOnce({
        ...project1,
        title: 'Updated Title',
        description: 'Updated description',
      })

      renderProjectDetail('project-1')

      fireEvent.click(await screen.findByRole('button', { name: /edit/i }))
      fillEditTitle('Updated Title')
      fireEvent.click(screen.getByRole('button', { name: /save/i }))

      expect(await screen.findByText('Updated Title')).toBeInTheDocument()
      expect(screen.getByText('Updated description')).toBeInTheDocument()
      expect(screen.queryByLabelText(/^title$/i)).not.toBeInTheDocument()
    })

    it('should show an error message and remain in edit mode when updateProject fails', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)
      mockedUpdateProject.mockRejectedValueOnce(new Error('프로젝트 수정에 실패했습니다'))

      renderProjectDetail('project-1')

      fireEvent.click(await screen.findByRole('button', { name: /edit/i }))
      fillEditTitle('Updated Title')
      fireEvent.click(screen.getByRole('button', { name: /save/i }))

      expect(await screen.findByText('프로젝트 수정에 실패했습니다')).toBeInTheDocument()
      expect(screen.getByLabelText(/^title$/i)).toBeInTheDocument()
    })
  })

  // T056a (delete trigger half): ProjectDetail had no way to actually
  // trigger the soft delete that removeProject()/DELETE /projects/{id}
  // already implement (T050/T053) — same kind of UI gap as the edit button.
  // Mirrors TrashedProjectCard's confirm-before-irreversible-ish-action
  // pattern (soft delete is recoverable via Trash, but still deserves a
  // confirm step to avoid a stray click).
  describe('deleting the project', () => {
    it('should render a Delete button once the project has loaded', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)

      renderProjectDetail('project-1')

      expect(await screen.findByRole('button', { name: /delete/i })).toBeInTheDocument()
    })

    it('should NOT call removeProject immediately when Delete is clicked, showing a confirm step instead', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)

      renderProjectDetail('project-1')

      fireEvent.click(await screen.findByRole('button', { name: /delete/i }))

      expect(mockedRemoveProject).not.toHaveBeenCalled()
      expect(screen.getByText(/정말 삭제/)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /확인/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /취소/ })).toBeInTheDocument()
    })

    it('should return to the normal view without calling removeProject when the confirm step is cancelled', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)

      renderProjectDetail('project-1')

      fireEvent.click(await screen.findByRole('button', { name: /delete/i }))
      fireEvent.click(screen.getByRole('button', { name: /취소/ }))

      expect(mockedRemoveProject).not.toHaveBeenCalled()
      expect(screen.queryByText(/정말 삭제/)).not.toBeInTheDocument()
      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
    })

    it('should call removeProject and navigate to the dashboard when the confirm step is confirmed', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)
      mockedRemoveProject.mockResolvedValueOnce(undefined)

      renderProjectDetail('project-1')

      fireEvent.click(await screen.findByRole('button', { name: /delete/i }))
      fireEvent.click(screen.getByRole('button', { name: /확인/ }))

      await waitFor(() => expect(mockedRemoveProject).toHaveBeenCalledWith('project-1'))
      expect(await screen.findByText('Dashboard Page')).toBeInTheDocument()
    })

    it('should show an error and stay on the page when removeProject fails', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)
      mockedRemoveProject.mockRejectedValueOnce(new Error('삭제에 실패했습니다'))

      renderProjectDetail('project-1')

      fireEvent.click(await screen.findByRole('button', { name: /delete/i }))
      fireEvent.click(screen.getByRole('button', { name: /확인/ }))

      expect(await screen.findByText('삭제에 실패했습니다')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /확인/ })).toBeInTheDocument()
    })
  })

  // T082: task list + creation slice.
  describe('task list', () => {
    it('should render each task returned by listTasks as a list item', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)
      mockedListTasks.mockReset()
      mockedListTasks.mockResolvedValueOnce([task1])

      renderProjectDetail('project-1')

      await screen.findByText('My First Project')
      expect(await screen.findAllByRole('listitem')).toHaveLength(1)
      expect(screen.getByText('Task 1: My First Task')).toBeInTheDocument()
    })

    it('should call listTasks with the current project id', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)

      renderProjectDetail('project-1')

      await screen.findByText('My First Project')
      await waitFor(() => expect(mockedListTasks).toHaveBeenCalledWith('project-1'))
    })

    it('should navigate to the task detail route when a task card is clicked', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)
      mockedListTasks.mockReset()
      mockedListTasks.mockResolvedValueOnce([task1])

      renderProjectDetail('project-1')

      fireEvent.click(await screen.findByText('Task 1: My First Task'))

      expect(await screen.findByText('Task Detail Page')).toBeInTheDocument()
    })

    it('should render a "작업 추가" button that opens CreateTaskModal', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)

      renderProjectDetail('project-1')

      fireEvent.click(await screen.findByRole('button', { name: '작업 추가' }))

      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('should close the modal and refetch tasks after a task is successfully created', async () => {
      mockedGetProject.mockResolvedValueOnce(project1)
      mockedListTasks.mockReset()
      mockedListTasks.mockResolvedValueOnce([]).mockResolvedValueOnce([task1])
      mockedCreateTask.mockResolvedValueOnce(task1)

      renderProjectDetail('project-1')

      fireEvent.click(await screen.findByRole('button', { name: '작업 추가' }))
      fireEvent.change(screen.getByLabelText(/^title$/i), {
        target: { value: 'My First Task' },
      })
      const file = new File(['code'], 'a.py', { type: 'text/plain' })
      fireEvent.change(screen.getByTestId('file-upload-input'), {
        target: { files: [file] },
      })
      fireEvent.click(screen.getByRole('button', { name: /create/i }))

      await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
      expect(await screen.findByText('Task 1: My First Task')).toBeInTheDocument()
    })
  })
})
