import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

// TaskCard (T079) does not exist yet — frontend/src/components/task/TaskCard.tsx
//
// Expected contract:
//   export interface TaskCardProps {
//     task: Task  // from @/services/task-service
//     onClick?: (task: Task) => void
//   }
//   export function TaskCard({ task, onClick }: TaskCardProps)
//
// Design decisions (mirrors ProjectCard):
//   - role="button" + tabIndex={0} + Enter key activation, calling
//     onClick?.(task).
//   - Displays "Task {task.task_number}: {task.title}" and the description.
//   - When task.uploaded_code is present, shows small badges for
//     detected_language / complexity_level / upload_method.
import { TaskCard } from '@/components/task/TaskCard'
import type { Task } from '@/services/task-service'

const baseTask: Task = {
  id: 'task-1',
  project_id: 'project-1',
  task_number: 1,
  title: 'My First Task',
  description: 'A simple task',
  upload_method: 'file',
  deletion_status: 'active',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  uploaded_code: {
    detected_language: 'python',
    complexity_level: 'beginner',
    total_lines: 42,
    total_files: 1,
    upload_size_bytes: 1024,
    files: [
      {
        file_name: 'main.py',
        file_path: null,
        file_extension: '.py',
        file_size_bytes: 1024,
      },
    ],
  },
}

describe('TaskCard', () => {
  it('should render the task number and title', () => {
    render(<TaskCard task={baseTask} />)

    expect(screen.getByText('Task 1: My First Task')).toBeInTheDocument()
  })

  it('should render the task description', () => {
    render(<TaskCard task={baseTask} />)

    expect(screen.getByText('A simple task')).toBeInTheDocument()
  })

  it('should render badges for detected_language, complexity_level and upload_method when uploaded_code is present', () => {
    render(<TaskCard task={baseTask} />)

    expect(screen.getByText(/python/i)).toBeInTheDocument()
    expect(screen.getByText(/beginner/i)).toBeInTheDocument()
    expect(screen.getByText(/file/i)).toBeInTheDocument()
  })

  it('should not throw when uploaded_code is null', () => {
    render(<TaskCard task={{ ...baseTask, uploaded_code: null }} />)

    expect(screen.getByText('Task 1: My First Task')).toBeInTheDocument()
  })

  it('should call onClick with the task when clicked', () => {
    const handleClick = vi.fn()
    render(<TaskCard task={baseTask} onClick={handleClick} />)

    fireEvent.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledWith(baseTask)
  })

  it('should call onClick with the task when activated via keyboard (Enter)', () => {
    const handleClick = vi.fn()
    render(<TaskCard task={baseTask} onClick={handleClick} />)

    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter', code: 'Enter' })

    expect(handleClick).toHaveBeenCalledWith(baseTask)
  })

  it('should not throw when clicked without an onClick prop', () => {
    render(<TaskCard task={baseTask} />)

    expect(() => fireEvent.click(screen.getByRole('button'))).not.toThrow()
  })
})
