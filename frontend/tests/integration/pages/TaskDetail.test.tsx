import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// TaskDetail page (T083) does not exist yet — frontend/src/pages/TaskDetail.tsx.
// It replaces the inline placeholder `function TaskDetail()` currently
// defined in frontend/src/App.tsx, at the route
// "/projects/:projectId/tasks/:taskId".
//
// Expected contract (mirrors ProjectDetail):
//   - Reads `taskId` from the route params and fetches it via
//     @/services/task-service#getTask(taskId), using TanStack Query.
//   - Loading state: role="status".
//   - Success: renders the task's title; a role="tablist" with 3
//     role="tab" entries ("Document" / "Practice" / "Q&A"); clicking a tab
//     switches the active tab (local state); each tab's content is a
//     placeholder only (Phase 6-8 fills it in later).
//   - Error/not-found: shows a message containing "찾을 수 없습니다".
import TaskDetail from '@/pages/TaskDetail'
import * as taskService from '@/services/task-service'
import { createTestQueryClient } from '../../test-utils/queryClient'

vi.mock('@/services/task-service')

// DocumentViewer (T108) renders the real Document tab content. It is mocked
// here because its own data-fetching/rendering is covered by
// tests/unit/components/document/DocumentViewer.test.tsx — this file only
// asserts that TaskDetail wires the Document tab to it with the right taskId.
vi.mock('@/components/document/DocumentViewer', () => ({
  DocumentViewer: ({ taskId }: { taskId: string }) => (
    <div data-testid="document-viewer">{taskId}</div>
  ),
}))

// PracticeViewer (T125) renders the real Practice tab content (T127). Mocked
// here for the same reason as DocumentViewer above.
vi.mock('@/components/practice/PracticeViewer', () => ({
  PracticeViewer: ({ taskId }: { taskId: string }) => (
    <div data-testid="practice-viewer">{taskId}</div>
  ),
}))

const mockedGetTask = taskService.getTask as unknown as ReturnType<typeof vi.fn>

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

function renderTaskDetail(projectId = 'project-1', taskId = 'task-1') {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/projects/${projectId}/tasks/${taskId}`]}>
        <Routes>
          <Route path="/projects/:projectId/tasks/:taskId" element={<TaskDetail />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('TaskDetail page', () => {
  beforeEach(() => {
    mockedGetTask.mockReset()
  })

  it('should show a loading state while the task is being fetched', () => {
    mockedGetTask.mockReturnValue(new Promise(() => {}))

    renderTaskDetail()

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('should fetch the task matching the :taskId route param', async () => {
    mockedGetTask.mockResolvedValueOnce(task1)

    renderTaskDetail('project-1', 'task-1')

    await screen.findByText('My First Task')
    expect(mockedGetTask).toHaveBeenCalledWith('task-1')
  })

  it('should render the task title once loaded', async () => {
    mockedGetTask.mockResolvedValueOnce(task1)

    renderTaskDetail()

    expect(await screen.findByText('My First Task')).toBeInTheDocument()
  })

  it('should render a tablist with Document/Practice/Q&A tabs', async () => {
    mockedGetTask.mockResolvedValueOnce(task1)

    renderTaskDetail()

    await screen.findByText('My First Task')
    expect(screen.getByRole('tablist')).toBeInTheDocument()
    const tabs = screen.getAllByRole('tab')
    expect(tabs).toHaveLength(3)
    expect(screen.getByRole('tab', { name: 'Document' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Practice' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Q&A' })).toBeInTheDocument()
  })

  it('should default to the Document tab as active', async () => {
    mockedGetTask.mockResolvedValueOnce(task1)

    renderTaskDetail()

    await screen.findByText('My First Task')
    expect(screen.getByRole('tab', { name: 'Document' })).toHaveAttribute(
      'aria-selected',
      'true',
    )
  })

  it('should switch the active tab when Practice is clicked', async () => {
    mockedGetTask.mockResolvedValueOnce(task1)

    renderTaskDetail()

    await screen.findByText('My First Task')
    fireEvent.click(screen.getByRole('tab', { name: 'Practice' }))

    expect(screen.getByRole('tab', { name: 'Practice' })).toHaveAttribute(
      'aria-selected',
      'true',
    )
    expect(screen.getByRole('tab', { name: 'Document' })).toHaveAttribute(
      'aria-selected',
      'false',
    )
  })

  it('should switch the active tab when Q&A is clicked', async () => {
    mockedGetTask.mockResolvedValueOnce(task1)

    renderTaskDetail()

    await screen.findByText('My First Task')
    fireEvent.click(screen.getByRole('tab', { name: 'Q&A' }))

    expect(screen.getByRole('tab', { name: 'Q&A' })).toHaveAttribute('aria-selected', 'true')
  })

  it('should render the DocumentViewer in the Document tab with the task id', async () => {
    mockedGetTask.mockResolvedValueOnce(task1)

    renderTaskDetail('project-1', 'task-1')

    await screen.findByText('My First Task')
    expect(screen.getByTestId('document-viewer')).toHaveTextContent('task-1')
  })

  it('should render the PracticeViewer in the Practice tab with the task id', async () => {
    mockedGetTask.mockResolvedValueOnce(task1)

    renderTaskDetail('project-1', 'task-1')

    await screen.findByText('My First Task')
    fireEvent.click(screen.getByRole('tab', { name: 'Practice' }))

    expect(screen.getByTestId('practice-viewer')).toHaveTextContent('task-1')
  })

  it('should show a not-found message when the task cannot be fetched (404)', async () => {
    mockedGetTask.mockRejectedValueOnce(new Error('작업을 찾을 수 없습니다'))

    renderTaskDetail('project-1', 'missing-id')

    expect(await screen.findByText(/찾을 수 없습니다/)).toBeInTheDocument()
  })
})
