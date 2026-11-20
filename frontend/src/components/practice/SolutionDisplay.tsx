import { useState } from 'react'

export interface SolutionDisplayProps {
  solution: string | null
  expectedOutput?: string | null
}

export function SolutionDisplay({ solution, expectedOutput }: SolutionDisplayProps) {
  const [revealed, setRevealed] = useState(false)

  if (!solution) {
    return null
  }

  if (!revealed) {
    return (
      <button type="button" onClick={() => setRevealed(true)}>
        정답 보기
      </button>
    )
  }

  return (
    <div>
      <pre>{solution}</pre>
      {expectedOutput && <p>{expectedOutput}</p>}
    </div>
  )
}
