import { useQuery } from '@tanstack/react-query'

import { getTaskPractice } from '../../services/practice-service'
import { HintReveal } from './HintReveal'
import { ProblemCard } from './ProblemCard'
import { SolutionDisplay } from './SolutionDisplay'

export interface PracticeViewerProps {
  taskId: string
}

export function PracticeViewer({ taskId }: PracticeViewerProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['practice', taskId],
    queryFn: () => getTaskPractice(taskId),
  })

  if (isLoading) {
    return <div role="status">실습 문제를 불러오는 중...</div>
  }

  if (isError || !data) {
    return <p>실습 문제를 불러오지 못했습니다</p>
  }

  if (data.status === 'pending') {
    return <div role="status">실습 문제를 생성하는 중입니다...</div>
  }

  return (
    <div>
      {data.problems.map((problem) => (
        <ProblemCard key={problem.problem_number} problem={problem}>
          {problem.hints && <HintReveal hints={problem.hints} />}
          <SolutionDisplay solution={problem.model_solution} expectedOutput={problem.expected_output} />
        </ProblemCard>
      ))}
    </div>
  )
}
