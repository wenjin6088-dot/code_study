import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Dashboard page (T054, creation flow T056) does not exist yet —
// frontend/src/pages/Dashboard.tsx. It replaces the inline placeholder
// `function Dashboard()` currently defined in frontend/src/App.tsx (that
// swap is GREEN-phase work; this test renders the page component directly).
//
// Expected contract:
//   - On mount, fetches the current user's projects via
//     @/services/project-service#listProjects, using TanStack Query
//     (useQuery({ queryKey: ['projects'], queryFn: listProjects })) so the
//     test must wrap the render in a QueryClientProvider — see
//     frontend/tests/test-utils/queryClient.ts (no app-wide test wrapper
//     existed before this, so one was added as test infra only).
//   - Loading state: a `role="status"` element while the query is pending.
//   - Empty state: once loaded, if the list is empty, shows a fixed message
//     containing "아직 프로젝트가 없습니다" (Korean, matching the rest of the
//     app's user-facing copy style) instead of any ProjectCards.
//   - Non-empty state: renders one ProjectCard (T051) per project; clicking
//     a card navigates to `/projects/{project.id}` (ProjectCard itself does
//     not navigate — Dashboard supplies the onClick that calls useNavigate).
//   - A "Create Project" button is always visible; clicking it opens
//     CreateProjectModal (T052) with isOpen=true.
//   - Creation flow (T056): CreateProjectModal's onCreate handler closes the
//     modal and invalidates/refetches the ['projects'] query so the newly
//     created project appears in the list without a full page reload. This
//     test simulates that by making the mocked listProjects return an
//     updated array on its second call.
import Dashboard from '@/pages/Dashboard'
import * as projectService from '@/services/project-service'
import { createTestQueryClient } from '../../test-utils/queryClient'

vi.mock('@/services/project-service')

const mockedListProjects = projectService.listProjects as unknown as ReturnType<typeof vi.fn>
const mockedCreateProject = projectService.createProject as unknown as ReturnType<typeof vi.fn>

const project1 = {
  id: 'project-1',
  title: 'My First Project',
  description: 'Learning FastAPI',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  last_activity_at: '2026-01-02T00:00:00Z',
}

const newProject = {
  id: 'project-2',
  title: 'Second Project',
  description: 'React practice',
  created_at: '2026-01-05T00:00:00Z',
  updated_at: '2026-01-05T00:00:00Z',
  last_activity_at: '2026-01-05T00:00:00Z',
}

function renderDashboard(initialEntries: string[] = ['/']) {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects/:projectId" element={<div>Project Detail Page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Dashboard page', () => {
  beforeEach(() => {
    mockedListProjects.mockReset()
    mockedCreateProject.mockReset()
  })

  it('should show a loading state while projects are being fetched', () => {
    mockedListProjects.mockReturnValue(new Promise(() => {}))

    renderDashboard()

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('should render a ProjectCard for each of the user\'s projects', async () => {
    mockedListProjects.mockResolvedValueOnce([project1])

    renderDashboard()

    expect(await screen.findByText('My First Project')).toBeInTheDocument()
  })

  it('should show an empty-state message when there are no projects', async () => {
    mockedListProjects.mockResolvedValueOnce([])

    renderDashboard()

    expect(await screen.findByText(/아직 프로젝트가 없습니다/)).toBeInTheDocument()
  })

  it('should always render a "Create Project" trigger button', async () => {
    mockedListProjects.mockResolvedValueOnce([])

    renderDashboard()

    expect(await screen.findByRole('button', { name: /create project/i })).toBeInTheDocument()
  })

  it('should open the CreateProjectModal when "Create Project" is clicked', async () => {
    mockedListProjects.mockResolvedValueOnce([])

    renderDashboard()

    fireEvent.click(await screen.findByRole('button', { name: /create project/i }))

    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('should navigate to the project detail route when a ProjectCard is clicked', async () => {
    mockedListProjects.mockResolvedValueOnce([project1])

    renderDashboard()

    fireEvent.click(await screen.findByText('My First Project'))

    expect(await screen.findByText('Project Detail Page')).toBeInTheDocument()
  })

  it('should show the newly created project in the list after a successful creation', async () => {
    mockedListProjects.mockResolvedValueOnce([project1])
    mockedListProjects.mockResolvedValueOnce([project1, newProject])
    mockedCreateProject.mockResolvedValueOnce(newProject)

    renderDashboard()

    expect(await screen.findByText('My First Project')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /create project/i }))
    fireEvent.change(screen.getByLabelText(/^title$/i), { target: { value: 'Second Project' } })
    fireEvent.click(screen.getByRole('button', { name: /^create$/i }))

    await waitFor(() => expect(screen.getByText('Second Project')).toBeInTheDocument())
    expect(mockedListProjects).toHaveBeenCalledTimes(2)
  })
})
