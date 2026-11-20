import { useState } from 'react'

export interface HintRevealProps {
  hints: string[]
}

export function HintReveal({ hints }: HintRevealProps) {
  const [revealedCount, setRevealedCount] = useState(0)

  if (hints.length === 0) {
    return null
  }

  return (
    <div>
      <ul>
        {hints.slice(0, revealedCount).map((hint, index) => (
          <li key={index}>{hint}</li>
        ))}
      </ul>
      {revealedCount < hints.length && (
        <button type="button" onClick={() => setRevealedCount((count) => count + 1)}>
          힌트 보기 ({revealedCount}/{hints.length})
        </button>
      )}
    </div>
  )
}
