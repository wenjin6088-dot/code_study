import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// CreateTaskModal (T081) does not exist yet —
// frontend/src/components/task/CreateTaskModal.tsx
//
// Expected contract (mirrors CreateProjectModal):
//   export interface CreateTaskModalProps {
//     isOpen: boolean
//     projectId: string
//     onClose: () => void
//     onCreate: (task: Task) => void
//   }
//
// Design decisions:
//   - Renders null when isOpen is false; role="dialog" when true.
//   - "Title"/"Description" labelled inputs.
//   - Three buttons/radios to switch upload method: "파일" / "폴더" / "붙여넣기",
//     defaulting to "파일", conditionally rendering FileUpload / FolderUpload /
//     PasteCode.
//   - Calls createTask(projectId, input) directly on submit (mirrors
//     CreateProjectModal calling createProject itself). On success calls
//     onCreate(task) (does not call onClose itself). On failure shows the
//     error message in role="alert".
//   - Submit button ("Create") is disabled when:
//       * title.trim().length < 5, OR
//       * upload method is file/folder and 0 files are selected, OR
//       * upload method is paste and content is empty.
import { CreateTaskModal } from '@/components/task/CreateTaskModal'
import * as taskService from '@/services/task-service'

vi.mock('@/services/task-service')

const mockedCreateTask = taskService.createTask as unknown as ReturnType<typeof vi.fn>

const createdTask = {
  id: 'task-1',
  project_id: 'project-1',
  task_number: 1,
  title: 'New Task Title',
  description: 'A description',
  upload_method: 'file' as const,
  deletion_status: 'active',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  uploaded_code: null,
}

function fillTitle(value: string) {
  fireEvent.change(screen.getByLabelText(/^title$/i), { target: { value } })
}

function makeFile(name: string) {
  return new File(['code'], name, { type: 'text/plain' })
}

describe('CreateTaskModal', () => {
  beforeEach(() => {
    mockedCreateTask.mockReset()
  })

  it('should render nothing when isOpen is false', () => {
    render(
      <CreateTaskModal
        isOpen={false}
        projectId="project-1"
        onClose={vi.fn()}
        onCreate={vi.fn()}
      />,
    )

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('should render the title/description fields and upload method switch when isOpen is true', () => {
    render(
      <CreateTaskModal isOpen projectId="project-1" onClose={vi.fn()} onCreate={vi.fn()} />,
    )

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByLabelText(/^title$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^description$/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '파일' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '폴더' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '붙여넣기' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
  })

  it('should default to the file upload method, rendering the file picker', () => {
    render(
      <CreateTaskModal isOpen projectId="project-1" onClose={vi.fn()} onCreate={vi.fn()} />,
    )

    expect(screen.getByTestId('file-upload-input')).toBeInTheDocument()
  })

  it('should switch to the folder upload method when "폴더" is clicked', () => {
    render(
      <CreateTaskModal isOpen projectId="project-1" onClose={vi.fn()} onCreate={vi.fn()} />,
    )

    fireEvent.click(screen.getByRole('button', { name: '폴더' }))

    expect(screen.getByTestId('folder-upload-input')).toBeInTheDocument()
  })

  it('should switch to the paste upload method when "붙여넣기" is clicked', () => {
    render(
      <CreateTaskModal isOpen projectId="project-1" onClose={vi.fn()} onCreate={vi.fn()} />,
    )

    fireEvent.click(screen.getByRole('button', { name: '붙여넣기' }))

    expect(screen.getByLabelText('코드 붙여넣기')).toBeInTheDocument()
    expect(screen.getByLabelText('언어 선택')).toBeInTheDocument()
  })

  it('should disable Create when the title is shorter than 5 characters', () => {
    render(
      <CreateTaskModal isOpen projectId="project-1" onClose={vi.fn()} onCreate={vi.fn()} />,
    )

    fillTitle('abcd')

    expect(screen.getByRole('button', { name: /create/i })).toBeDisabled()
  })

  it('should disable Create for the file method until a file is selected', () => {
    render(
      <CreateTaskModal isOpen projectId="project-1" onClose={vi.fn()} onCreate={vi.fn()} />,
    )

    fillTitle('My New Task')

    expect(screen.getByRole('button', { name: /create/i })).toBeDisabled()

    const input = screen.getByTestId('file-upload-input') as HTMLInputElement
    fireEvent.change(input, { target: { files: [makeFile('a.py')] } })

    expect(screen.getByRole('button', { name: /create/i })).toBeEnabled()
  })

  it('should disable Create for the paste method until content is entered', () => {
    render(
      <CreateTaskModal isOpen projectId="project-1" onClose={vi.fn()} onCreate={vi.fn()} />,
    )

    fillTitle('My New Task')
    fireEvent.click(screen.getByRole('button', { name: '붙여넣기' }))

    expect(screen.getByRole('button', { name: /create/i })).toBeDisabled()

    fireEvent.change(screen.getByLabelText('코드 붙여넣기'), { target: { value: 'print(1)' } })

    expect(screen.getByRole('button', { name: /create/i })).toBeEnabled()
  })

  it('should call onClose when Cancel is clicked, without calling createTask', () => {
    const handleClose = vi.fn()
    render(
      <CreateTaskModal
        isOpen
        projectId="project-1"
        onClose={handleClose}
        onCreate={vi.fn()}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))

    expect(handleClose).toHaveBeenCalledTimes(1)
    expect(mockedCreateTask).not.toHaveBeenCalled()
  })

  it('should call createTask with a file upload input on submit', async () => {
    mockedCreateTask.mockResolvedValueOnce(createdTask)
    render(
      <CreateTaskModal isOpen projectId="project-1" onClose={vi.fn()} onCreate={vi.fn()} />,
    )

    fillTitle('My New Task')
    fireEvent.change(screen.getByLabelText(/^description$/i), { target: { value: 'desc' } })
    const file1 = makeFile('a.py')
    fireEvent.change(screen.getByTestId('file-upload-input'), { target: { files: [file1] } })
    fireEvent.click(screen.getByRole('button', { name: /create/i }))

    await waitFor(() =>
      expect(mockedCreateTask).toHaveBeenCalledWith('project-1', {
        title: 'My New Task',
        description: 'desc',
        uploadMethod: 'file',
        files: [file1],
      }),
    )
  })

  it('should call createTask with a paste upload input, using the selected language option filename, on submit', async () => {
    mockedCreateTask.mockResolvedValueOnce(createdTask)
    render(
      <CreateTaskModal isOpen projectId="project-1" onClose={vi.fn()} onCreate={vi.fn()} />,
    )

    fillTitle('My New Task')
    fireEvent.click(screen.getByRole('button', { name: '붙여넣기' }))
    fireEvent.change(screen.getByLabelText('코드 붙여넣기'), { target: { value: 'print(1)' } })
    fireEvent.change(screen.getByLabelText('언어 선택'), { target: { value: 'javascript' } })
    fireEvent.click(screen.getByRole('button', { name: /create/i }))

    await waitFor(() =>
      expect(mockedCreateTask).toHaveBeenCalledWith('project-1', {
        title: 'My New Task',
        description: undefined,
        uploadMethod: 'paste',
        pasteContent: 'print(1)',
        pasteFilename: 'pasted.js',
      }),
    )
  })

  it('should call onCreate with the created task after a successful submit', async () => {
    mockedCreateTask.mockResolvedValueOnce(createdTask)
    const handleCreate = vi.fn()
    render(
      <CreateTaskModal
        isOpen
        projectId="project-1"
        onClose={vi.fn()}
        onCreate={handleCreate}
      />,
    )

    fillTitle('My New Task')
    fireEvent.change(screen.getByTestId('file-upload-input'), {
      target: { files: [makeFile('a.py')] },
    })
    fireEvent.click(screen.getByRole('button', { name: /create/i }))

    await waitFor(() => expect(handleCreate).toHaveBeenCalledWith(createdTask))
  })

  it('should show an error message and not call onCreate when createTask fails', async () => {
    mockedCreateTask.mockRejectedValueOnce(new Error('작업 생성에 실패했습니다'))
    const handleCreate = vi.fn()
    const handleClose = vi.fn()
    render(
      <CreateTaskModal
        isOpen
        projectId="project-1"
        onClose={handleClose}
        onCreate={handleCreate}
      />,
    )

    fillTitle('My New Task')
    fireEvent.change(screen.getByTestId('file-upload-input'), {
      target: { files: [makeFile('a.py')] },
    })
    fireEvent.click(screen.getByRole('button', { name: /create/i }))

    expect(await screen.findByText('작업 생성에 실패했습니다')).toBeInTheDocument()
    expect(handleCreate).not.toHaveBeenCalled()
    expect(handleClose).not.toHaveBeenCalled()
  })
})
