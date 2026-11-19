import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

// Chapter1Summary (T102) does not exist yet —
// frontend/src/components/document/chapters/Chapter1.tsx
import { Chapter1Summary } from '@/components/document/chapters/Chapter1'
import type { DocumentChapter1 } from '@/services/document-service'

const chapter: DocumentChapter1 = {
  title: 'What This Code Does',
  summary: 'It adds two numbers together.',
}

describe('Chapter1Summary', () => {
  it('should render the chapter title as a heading', () => {
    render(<Chapter1Summary chapter={chapter} />)

    expect(screen.getByRole('heading', { name: 'What This Code Does' })).toBeInTheDocument()
  })

  it('should render the one-sentence summary', () => {
    render(<Chapter1Summary chapter={chapter} />)

    expect(screen.getByText('It adds two numbers together.')).toBeInTheDocument()
  })
})
