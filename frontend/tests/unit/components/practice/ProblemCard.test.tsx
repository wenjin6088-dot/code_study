import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

// ProblemCard (T122) does not exist yet — frontend/src/components/practice/ProblemCard.tsx
import { ProblemCard } from '@/components/practice/ProblemCard'
import type { PracticeProblem } from '@/services/practice-service'

const problem: PracticeProblem = {
  problem_number: 2,
  problem_type: 'fill_blanks',
  problem_statement: 'Fill in the missing operator.',
  learning_objective: 'Practice arithmetic operators.',
  hints: ['Hint 1'],
  model_solution: 'x = 1 + 1',
  expected_output: '2',
}

describe('ProblemCard', () => {
  it('should render the problem number, difficulty badge, and statement', () => {
    render(<ProblemCard problem={problem} />)

    expect(screen.getByText(/2/)).toBeInTheDocument()
    expect(screen.getByText('Fill Blanks')).toBeInTheDocument()
    expect(screen.getByText('Fill in the missing operator.')).toBeInTheDocument()
  })

  it('should render the learning objective when present', () => {
    render(<ProblemCard problem={problem} />)

    expect(screen.getByText('Practice arithmetic operators.')).toBeInTheDocument()
  })

  it('should map each problem_type to its English difficulty label', () => {
    const types: Array<[PracticeProblem['problem_type'], string]> = [
      ['follow_along', 'Follow Along'],
      ['fill_blanks', 'Fill Blanks'],
      ['modify', 'Modify'],
      ['debug', 'Debug'],
      ['create', 'Create'],
    ]

    types.forEach(([problem_type, label]) => {
      const { unmount } = render(
        <ProblemCard problem={{ ...problem, problem_type }} />,
      )
      expect(screen.getByText(label)).toBeInTheDocument()
      unmount()
    })
  })

  it('should render children inside the card', () => {
    render(
      <ProblemCard problem={problem}>
        <div data-testid="child">child content</div>
      </ProblemCard>,
    )

    expect(screen.getByTestId('child')).toBeInTheDocument()
  })
})
