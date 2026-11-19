import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// CreateProjectModal (T052) does not exist yet —
// frontend/src/components/project/CreateProjectModal.tsx
//
// Expected contract:
//   export interface CreateProjectModalProps {
//     isOpen: boolean
//     onClose: () => void
//     onCreate: (project: Project) => void
//   }
//   export function CreateProjectModal({ isOpen, onClose, onCreate }: CreateProjectModalProps)
//
// Design decisions (documented for the GREEN-phase implementer):
//   - Renders null when isOpen is false. When true, renders a dialog
//     (role="dialog") with:
//       * a "Title" labelled text input (required)
//       * a "Description" labelled text input (optional)
//       * a submit button named "Create", DISABLED while the trimmed title
//         is empty (satisfies "validates title non-empty before allowing
//         submit")
//       * a "Cancel" button that calls onClose() and performs no API call
//   - CreateProjectModal calls `createProject` from @/services/project-service
//     DIRECTLY on submit (it does not delegate the API call up to its
//     parent) — mirrors LoginForm calling `login()` itself. On success it
//     calls `onCreate(project)` with the created project returned by the
//     service. It does NOT call onClose() itself on success; the parent
//     (Dashboard) decides whether to close the modal from its onCreate
//     handler. This keeps the modal's responsibility limited to "create +
//     report the result".
//   - On failure, shows the thrown error's message in a `role="alert"`
//     element and does NOT call onCreate; the modal stays open (onClose is
//     not called either).
//   - An empty/whitespace-only description is sent as `undefined` (omitted
//     meaning), not as an empty string, to match project-service's optional
//     `description` field.
import { CreateProjectModal } from '@/components/project/CreateProjectModal'
import * as projectService from '@/services/project-service'

vi.mock('@/services/project-service')

const mockedCreateProject = projectService.createProject as unknown as ReturnType<typeof vi.fn>

const createdProject = {
  id: 'project-2',
  title: 'New Project',
  description: 'A new one',
  created_at: '2026-01-03T00:00:00Z',
  updated_at: '2026-01-03T00:00:00Z',
  last_activity_at: '2026-01-03T00:00:00Z',
}

function fillTitle(value: string) {
  fireEvent.change(screen.getByLabelText(/^title$/i), { target: { value } })
}

describe('CreateProjectModal', () => {
  beforeEach(() => {
    mockedCreateProject.mockReset()
  })

  it('should render nothing when isOpen is false', () => {
    render(<CreateProjectModal isOpen={false} onClose={vi.fn()} onCreate={vi.fn()} />)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('should render the title and description fields and action buttons when isOpen is true', () => {
    render(<CreateProjectModal isOpen onClose={vi.fn()} onCreate={vi.fn()} />)

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByLabelText(/^title$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^description$/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
  })

  it('should disable the Create button while the title is empty', () => {
    render(<CreateProjectModal isOpen onClose={vi.fn()} onCreate={vi.fn()} />)

    expect(screen.getByRole('button', { name: /create/i })).toBeDisabled()
  })

  it('should enable the Create button once a non-empty title is entered', () => {
    render(<CreateProjectModal isOpen onClose={vi.fn()} onCreate={vi.fn()} />)

    fillTitle('New Project')

    expect(screen.getByRole('button', { name: /create/i })).toBeEnabled()
  })

  it('should keep the Create button disabled for a whitespace-only title', () => {
    render(<CreateProjectModal isOpen onClose={vi.fn()} onCreate={vi.fn()} />)

    fillTitle('   ')

    expect(screen.getByRole('button', { name: /create/i })).toBeDisabled()
  })

  it('should call onClose when Cancel is clicked, without calling createProject', () => {
    const handleClose = vi.fn()
    render(<CreateProjectModal isOpen onClose={handleClose} onCreate={vi.fn()} />)

    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))

    expect(handleClose).toHaveBeenCalledTimes(1)
    expect(mockedCreateProject).not.toHaveBeenCalled()
  })

  it('should call createProject with the entered title and description on submit', async () => {
    mockedCreateProject.mockResolvedValueOnce(createdProject)
    render(<CreateProjectModal isOpen onClose={vi.fn()} onCreate={vi.fn()} />)

    fillTitle('New Project')
    fireEvent.change(screen.getByLabelText(/^description$/i), { target: { value: 'A new one' } })
    fireEvent.click(screen.getByRole('button', { name: /create/i }))

    await waitFor(() =>
      expect(mockedCreateProject).toHaveBeenCalledWith({
        title: 'New Project',
        description: 'A new one',
      }),
    )
  })

  it('should omit description when left blank', async () => {
    mockedCreateProject.mockResolvedValueOnce(createdProject)
    render(<CreateProjectModal isOpen onClose={vi.fn()} onCreate={vi.fn()} />)

    fillTitle('New Project')
    fireEvent.click(screen.getByRole('button', { name: /create/i }))

    await waitFor(() =>
      expect(mockedCreateProject).toHaveBeenCalledWith({
        title: 'New Project',
        description: undefined,
      }),
    )
  })

  it('should call onCreate with the created project after a successful submit', async () => {
    mockedCreateProject.mockResolvedValueOnce(createdProject)
    const handleCreate = vi.fn()
    render(<CreateProjectModal isOpen onClose={vi.fn()} onCreate={handleCreate} />)

    fillTitle('New Project')
    fireEvent.click(screen.getByRole('button', { name: /create/i }))

    await waitFor(() => expect(handleCreate).toHaveBeenCalledWith(createdProject))
  })

  it('should show an error message and not call onCreate when createProject fails', async () => {
    mockedCreateProject.mockRejectedValueOnce(new Error('제목을 입력해 주세요'))
    const handleCreate = vi.fn()
    const handleClose = vi.fn()
    render(<CreateProjectModal isOpen onClose={handleClose} onCreate={handleCreate} />)

    fillTitle('New Project')
    fireEvent.click(screen.getByRole('button', { name: /create/i }))

    expect(await screen.findByText('제목을 입력해 주세요')).toBeInTheDocument()
    expect(handleCreate).not.toHaveBeenCalled()
    expect(handleClose).not.toHaveBeenCalled()
  })
})
