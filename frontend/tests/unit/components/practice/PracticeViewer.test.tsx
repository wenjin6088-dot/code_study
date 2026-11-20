import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// PracticeViewer (T125) does not exist yet — frontend/src/components/practice/PracticeViewer.tsx
import { PracticeViewer } from '@/components/practice/PracticeViewer'
import { getTaskPractice } from '@/services/practice-service'
import { createTestQueryClient } from '../../../test-utils/queryClient'

vi.mock('@/services/practice-service')

const mockedGetTaskPractice = getTaskPractice as unknown as ReturnType<typeof vi.fn>

function renderViewer(taskId = 'task-1') {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <PracticeViewer taskId={taskId} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  mockedGetTaskPractice.mockReset()
})

const PROBLEM_TYPES = ['follow_along', 'fill_blanks', 'modify', 'debug', 'create'] as const

function makeProblems() {
  return PROBLEM_TYPES.map((problem_type, index) => ({
    problem_number: index + 1,
    problem_type,
    problem_statement: `Statement ${index + 1}`,
    learning_objective: `Objective ${index + 1}`,
    hints: ['Hint 1', 'Hint 2'],
    model_solution: `Solution ${index + 1}`,
    expected_output: `Output ${index + 1}`,
  }))
}

describe('PracticeViewer', () => {
  it('should show a loading state while fetching', () => {
    mockedGetTaskPractice.mockReturnValue(new Promise(() => {}))

    renderViewer()

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('should show a generating message while practice problems are pending', async () => {
    mockedGetTaskPractice.mockResolvedValue({
      task_id: 'task-1',
      status: 'pending',
      problems: [],
    })

    renderViewer()

    expect(await screen.findByText(/생성하는 중/)).toBeInTheDocument()
  })

  it('should render all 5 problems with their difficulty labels when completed', async () => {
    mockedGetTaskPractice.mockResolvedValue({
      task_id: 'task-1',
      status: 'completed',
      problems: makeProblems(),
    })

    renderViewer()

    expect(await screen.findByText('Statement 1')).toBeInTheDocument()
    expect(screen.getByText('Follow Along')).toBeInTheDocument()
    expect(screen.getByText('Fill Blanks')).toBeInTheDocument()
    expect(screen.getByText('Modify')).toBeInTheDocument()
    expect(screen.getByText('Debug')).toBeInTheDocument()
    expect(screen.getByText('Create')).toBeInTheDocument()
  })

  it('should show an error message when the request fails', async () => {
    mockedGetTaskPractice.mockRejectedValue(new Error('network error'))

    renderViewer()

    expect(await screen.findByText(/불러오지 못했습니다/)).toBeInTheDocument()
  })
})
