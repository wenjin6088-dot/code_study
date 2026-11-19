import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// TrashedProjectCard (T178, projects-only scope) does not exist yet —
// frontend/src/components/trash/TrashedProjectCard.tsx
//
// Expected contract:
//   export interface TrashedProjectCardProps {
//     project: Project
//     onRestore: (project: Project) => void
//     onPermanentDelete: (project: Project) => void
//   }
//
// Design decisions (mirrors CreateProjectModal/ProjectDetail's "component
// calls the service itself" pattern):
//   - Renders the project's title/description and two buttons: "복원"
//     (Restore) and "영구 삭제" (Permanent delete).
//   - "복원" calls restoreProject(project.id) from @/services/trash-service
//     directly. On success, calls onRestore(restoredProject). On failure,
//     shows the error message in a role="alert" element and does not call
//     onRestore.
//   - "영구 삭제" is irreversible, so it does NOT call the API immediately.
//     Clicking it switches to a confirm state showing "정말 영구적으로
//     삭제하시겠습니까?" plus "확인"/"취소" buttons (no native
//     window.confirm — keeps the flow testable and in-page). "취소" returns
//     to the normal view without any API call. "확인" calls
//     permanentDeleteProject(project.id); on success calls
//     onPermanentDelete(project); on failure shows the error in role="alert"
//     and stays in the confirm state.
import { TrashedProjectCard } from '@/components/trash/TrashedProjectCard'
import * as trashService from '@/services/trash-service'

vi.mock('@/services/trash-service')

const mockedRestoreProject = trashService.restoreProject as unknown as ReturnType<
  typeof vi.fn
>
const mockedPermanentDeleteProject =
  trashService.permanentDeleteProject as unknown as ReturnType<typeof vi.fn>

const trashedProject = {
  id: 'project-1',
  title: 'Trashed Project',
  description: 'Was deleted',
  deletion_status: 'trashed',
}

describe('TrashedProjectCard', () => {
  beforeEach(() => {
    mockedRestoreProject.mockReset()
    mockedPermanentDeleteProject.mockReset()
  })

  it('should render the project title, description, and action buttons', () => {
    render(
      <TrashedProjectCard
        project={trashedProject}
        onRestore={vi.fn()}
        onPermanentDelete={vi.fn()}
      />,
    )

    expect(screen.getByText('Trashed Project')).toBeInTheDocument()
    expect(screen.getByText('Was deleted')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /복원/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /영구 삭제/ })).toBeInTheDocument()
  })

  it('should call restoreProject and onRestore when 복원 succeeds', async () => {
    const restored = { ...trashedProject, deletion_status: 'active' }
    mockedRestoreProject.mockResolvedValueOnce(restored)
    const handleRestore = vi.fn()

    render(
      <TrashedProjectCard
        project={trashedProject}
        onRestore={handleRestore}
        onPermanentDelete={vi.fn()}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: /복원/ }))

    await waitFor(() => expect(mockedRestoreProject).toHaveBeenCalledWith('project-1'))
    await waitFor(() => expect(handleRestore).toHaveBeenCalledWith(restored))
  })

  it('should show an error and not call onRestore when 복원 fails', async () => {
    mockedRestoreProject.mockRejectedValueOnce(new Error('복원에 실패했습니다'))
    const handleRestore = vi.fn()

    render(
      <TrashedProjectCard
        project={trashedProject}
        onRestore={handleRestore}
        onPermanentDelete={vi.fn()}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: /복원/ }))

    expect(await screen.findByText('복원에 실패했습니다')).toBeInTheDocument()
    expect(handleRestore).not.toHaveBeenCalled()
  })

  it('should NOT call permanentDeleteProject immediately when 영구 삭제 is clicked, showing a confirm step instead', () => {
    render(
      <TrashedProjectCard
        project={trashedProject}
        onRestore={vi.fn()}
        onPermanentDelete={vi.fn()}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /영구 삭제/ }))

    expect(mockedPermanentDeleteProject).not.toHaveBeenCalled()
    expect(screen.getByText(/정말 영구적으로 삭제/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /확인/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /취소/ })).toBeInTheDocument()
  })

  it('should return to the normal view without calling the API when the confirm step is cancelled', () => {
    render(
      <TrashedProjectCard
        project={trashedProject}
        onRestore={vi.fn()}
        onPermanentDelete={vi.fn()}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /영구 삭제/ }))
    fireEvent.click(screen.getByRole('button', { name: /취소/ }))

    expect(mockedPermanentDeleteProject).not.toHaveBeenCalled()
    expect(screen.queryByText(/정말 영구적으로 삭제/)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /영구 삭제/ })).toBeInTheDocument()
  })

  it('should call permanentDeleteProject and onPermanentDelete when the confirm step is confirmed', async () => {
    mockedPermanentDeleteProject.mockResolvedValueOnce(undefined)
    const handlePermanentDelete = vi.fn()

    render(
      <TrashedProjectCard
        project={trashedProject}
        onRestore={vi.fn()}
        onPermanentDelete={handlePermanentDelete}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /영구 삭제/ }))
    fireEvent.click(screen.getByRole('button', { name: /확인/ }))

    await waitFor(() =>
      expect(mockedPermanentDeleteProject).toHaveBeenCalledWith('project-1'),
    )
    await waitFor(() =>
      expect(handlePermanentDelete).toHaveBeenCalledWith(trashedProject),
    )
  })

  it('should show an error and stay in the confirm state when permanent delete fails', async () => {
    mockedPermanentDeleteProject.mockRejectedValueOnce(new Error('삭제에 실패했습니다'))
    const handlePermanentDelete = vi.fn()

    render(
      <TrashedProjectCard
        project={trashedProject}
        onRestore={vi.fn()}
        onPermanentDelete={handlePermanentDelete}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /영구 삭제/ }))
    fireEvent.click(screen.getByRole('button', { name: /확인/ }))

    expect(await screen.findByText('삭제에 실패했습니다')).toBeInTheDocument()
    expect(handlePermanentDelete).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: /확인/ })).toBeInTheDocument()
  })
})
