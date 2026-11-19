import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

// Chapter2Prerequisites (T103) does not exist yet —
// frontend/src/components/document/chapters/Chapter2.tsx
import { Chapter2Prerequisites } from '@/components/document/chapters/Chapter2'
import type { DocumentChapter2 } from '@/services/document-service'

const chapter: DocumentChapter2 = {
  title: 'Prerequisites Knowledge',
  concepts: [
    {
      name: 'Variables',
      explanation: 'A named place to store a value.',
      analogy: 'Like a labeled box.',
      example: 'x = 1',
      use_cases: 'Storing numbers, text, anything.',
    },
    {
      name: 'Functions',
      explanation: 'A reusable block of code.',
      analogy: 'Like a recipe.',
      example: 'def add(a, b): return a + b',
      use_cases: 'Avoiding repeated code.',
    },
  ],
}

describe('Chapter2Prerequisites', () => {
  it('should render the chapter title', () => {
    render(<Chapter2Prerequisites chapter={chapter} />)

    expect(screen.getByRole('heading', { name: 'Prerequisites Knowledge' })).toBeInTheDocument()
  })

  it('should render a concept card for each concept with its name, explanation, analogy, example and use_cases', () => {
    render(<Chapter2Prerequisites chapter={chapter} />)

    expect(screen.getByText('Variables')).toBeInTheDocument()
    expect(screen.getByText('A named place to store a value.')).toBeInTheDocument()
    expect(screen.getByText('Like a labeled box.')).toBeInTheDocument()
    expect(screen.getByText('x = 1')).toBeInTheDocument()
    expect(screen.getByText('Storing numbers, text, anything.')).toBeInTheDocument()

    expect(screen.getByText('Functions')).toBeInTheDocument()
    expect(screen.getByText('A reusable block of code.')).toBeInTheDocument()
  })
})
