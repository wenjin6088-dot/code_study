import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Chapter4LineByLine (T104) does not exist yet —
// frontend/src/components/document/chapters/Chapter4.tsx
//
// Renders chapter4's line-by-line explanations in order, and supports an
// `activeIndex` prop (driven by DocumentViewer's sync scroll, see T105) that
// marks one entry as active and scrolls it into view.
import { Chapter4LineByLine } from '@/components/document/chapters/Chapter4'
import type { DocumentChapter4 } from '@/services/document-service'

const chapter: DocumentChapter4 = {
  title: 'Line-by-Line Explanation',
  explanations: [
    {
      file: 'main.py',
      line_start: 1,
      line_end: 1,
      code: 'x = 1',
      what_it_does: 'Assigns 1 to x.',
      syntax_breakdown: '`=` is assignment.',
      analogy: 'Putting a value in a labeled box.',
      alternative_example: 'x = 1 + 0',
      notes: 'x is now an int.',
    },
    {
      file: 'main.py',
      line_start: 2,
      line_end: 2,
      code: 'y = 2',
      what_it_does: 'Assigns 2 to y.',
      syntax_breakdown: '`=` is assignment.',
      analogy: 'Putting another value in another box.',
      alternative_example: 'y = 2 + 0',
      notes: 'y is now an int.',
    },
  ],
}

beforeEach(() => {
  Element.prototype.scrollIntoView = vi.fn()
})

describe('Chapter4LineByLine', () => {
  it('should render the chapter title', () => {
    render(<Chapter4LineByLine chapter={chapter} />)

    expect(screen.getByRole('heading', { name: 'Line-by-Line Explanation' })).toBeInTheDocument()
  })

  it('should render every explanation entry with its code and breakdown', () => {
    render(<Chapter4LineByLine chapter={chapter} />)

    expect(screen.getByText('x = 1')).toBeInTheDocument()
    expect(screen.getByText('Assigns 1 to x.')).toBeInTheDocument()
    expect(screen.getByText('y = 2')).toBeInTheDocument()
    expect(screen.getByText('Assigns 2 to y.')).toBeInTheDocument()
  })

  it('should mark the entry at activeIndex as active', () => {
    render(<Chapter4LineByLine chapter={chapter} activeIndex={1} />)

    const items = screen.getAllByRole('listitem')
    expect(items[1]).toHaveAttribute('aria-current', 'true')
    expect(items[0]).not.toHaveAttribute('aria-current', 'true')
  })

  it('should scroll the active entry into view when activeIndex changes', () => {
    const { rerender } = render(<Chapter4LineByLine chapter={chapter} />)

    rerender(<Chapter4LineByLine chapter={chapter} activeIndex={1} />)

    expect(Element.prototype.scrollIntoView).toHaveBeenCalled()
  })
})
