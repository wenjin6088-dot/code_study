import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Trash page (T181, projects-only scope) does not exist yet —
// frontend/src/pages/Trash.tsx. It replaces the inline placeholder
// `function Trash()` currently defined in frontend/src/App.tsx (GREEN-phase
// work; this test renders the page component directly).
//
// Expected contract (mirrors Dashboard):
//   - On mount, fetches trashed projects via
//     @/services/trash-service#listTrash, using TanStack Query
//     (useQuery({ queryKey: ['trash'], queryFn: listTrash })).
//   - Loading state: a role="status" element while pending.
//   - Empty state: "휴지통이 비어 있습니다" when the list is empty.
//   - Non-empty: renders one TrashedProjectCard (T178) per trashed project.
//   - TrashedProjectCard's onRestore/onPermanentDelete handlers invalidate
//     the ['trash'] query so the list re-fetches and the acted-on project
//     disappears, without a full page reload.
import Trash from '@/pages/Trash'
import * as trashService from '@/services/trash-service'
import { createTestQueryClient } from '../../test-utils/queryClient'

vi.mock('@/services/trash-service')

const mockedListTrash = trashService.listTrash as unknown as ReturnType<typeof vi.fn>
const mockedRestoreProject = trashService.restoreProject as unknown as ReturnType<
  typeof vi.fn
>
const mockedPermanentDeleteProject =
  trashService.permanentDeleteProject as unknown as ReturnType<typeof vi.fn>

const trashedProject1 = {
  id: 'project-1',
  title: 'Trashed One',
  description: 'First trashed project',
  deletion_status: 'trashed',
}

const trashedProject2 = {
  id: 'project-2',
  title: 'Trashed Two',
  description: 'Second trashed project',
  deletion_status: 'trashed',
}

function renderTrash() {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/trash']}>
        <Trash />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Trash page', () => {
  beforeEach(() => {
    mockedListTrash.mockReset()
    mockedRestoreProject.mockReset()
    mockedPermanentDeleteProject.mockReset()
  })

  it('should show a loading state while trashed projects are being fetched', () => {
    mockedListTrash.mockReturnValue(new Promise(() => {}))

    renderTrash()

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('should show an empty-state message when there is nothing in the trash', async () => {
    mockedListTrash.mockResolvedValueOnce([])

    renderTrash()

    expect(await screen.findByText(/휴지통이 비어 있습니다/)).toBeInTheDocument()
  })

  it('should render a TrashedProjectCard for each trashed project', async () => {
    mockedListTrash.mockResolvedValueOnce([trashedProject1, trashedProject2])

    renderTrash()

    expect(await screen.findByText('Trashed One')).toBeInTheDocument()
    expect(screen.getByText('Trashed Two')).toBeInTheDocument()
  })

  it('should remove a project from the list after it is restored', async () => {
    mockedListTrash.mockResolvedValueOnce([trashedProject1])
    mockedListTrash.mockResolvedValueOnce([])
    mockedRestoreProject.mockResolvedValueOnce({
      ...trashedProject1,
      deletion_status: 'active',
    })

    renderTrash()

    expect(await screen.findByText('Trashed One')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /복원/ }))

    await waitFor(() => expect(screen.queryByText('Trashed One')).not.toBeInTheDocument())
    expect(mockedListTrash).toHaveBeenCalledTimes(2)
  })

  it('should remove a project from the list after it is permanently deleted', async () => {
    mockedListTrash.mockResolvedValueOnce([trashedProject1])
    mockedListTrash.mockResolvedValueOnce([])
    mockedPermanentDeleteProject.mockResolvedValueOnce(undefined)

    renderTrash()

    expect(await screen.findByText('Trashed One')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /영구 삭제/ }))
    fireEvent.click(screen.getByRole('button', { name: /확인/ }))

    await waitFor(() => expect(screen.queryByText('Trashed One')).not.toBeInTheDocument())
    expect(mockedListTrash).toHaveBeenCalledTimes(2)
  })
})
