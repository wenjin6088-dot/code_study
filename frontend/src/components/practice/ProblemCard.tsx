import type { ReactNode } from 'react'

import type { PracticeProblem } from '../../services/practice-service'

const PROBLEM_TYPE_LABELS: Record<PracticeProblem['problem_type'], string> = {
  follow_along: 'Follow Along',
  fill_blanks: 'Fill Blanks',
  modify: 'Modify',
  debug: 'Debug',
  create: 'Create',
}

export interface ProblemCardProps {
  problem: PracticeProblem
  children?: ReactNode
}

export function ProblemCard({ problem, children }: ProblemCardProps) {
  return (
    <article aria-label={`문제 ${problem.problem_number}`}>
      <h2>문제 {problem.problem_number}</h2>
      <span>{PROBLEM_TYPE_LABELS[problem.problem_type]}</span>
      <h3>{problem.problem_statement}</h3>
      {problem.learning_objective && <p>{problem.learning_objective}</p>}
      {children}
    </article>
  )
}
