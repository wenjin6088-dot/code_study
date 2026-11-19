import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

// ExplanationPanel (T101) does not exist yet —
// frontend/src/components/document/ExplanationPanel.tsx
//
// Renders chapter navigation (role="tablist" with 7 tabs, one per chapter)
// plus the active chapter's content. Chapters 1, 2 and 4 delegate to their
// dedicated components (T102-T104); chapters 3, 5, 6, 7 are rendered inline.
import { ExplanationPanel } from '@/components/document/ExplanationPanel'
import type { DocumentContent } from '@/services/document-service'

const document: DocumentContent = {
  chapter1: { title: 'What This Code Does', summary: 'It adds numbers.' },
  chapter2: {
    title: 'Prerequisites Knowledge',
    concepts: [
      {
        name: 'Variables',
        explanation: 'A named place to store a value.',
        analogy: 'Like a labeled box.',
        example: 'x = 1',
        use_cases: 'Storing values.',
      },
    ],
  },
  chapter3: {
    title: 'Code Structure Overview',
    flowchart: 'flowchart TD\nA --> B',
    file_breakdown: { 'main.py': 'Entry point.' },
  },
  chapter4: {
    title: 'Line-by-Line Explanation',
    explanations: [
      {
        file: 'main.py',
        line_start: 1,
        line_end: 1,
        code: 'x = 1',
        what_it_does: 'Assigns 1 to x.',
        syntax_breakdown: '`=` is assignment.',
        analogy: 'Putting a value in a box.',
        alternative_example: 'x = 1 + 0',
        notes: 'x is now an int.',
      },
    ],
  },
  chapter5: {
    title: 'Execution Flow Simulation',
    steps: [{ step: 1, description: 'x is set to 1.', data_state: 'x=1' }],
  },
  chapter6: {
    title: 'Core Concepts Summary',
    concepts: [
      { name: 'Assignment', what_it_is: 'Storing a value.', why_used: 'To keep state.', where_applied: 'main.py' },
    ],
  },
  chapter7: {
    title: 'Common Mistakes',
    mistakes: [{ wrong: 'x = ', right: 'x = 1', why: 'Syntax error.', fix: 'Add a value.' }],
  },
}

describe('ExplanationPanel', () => {
  it('should render a tab for each of the 7 chapters', () => {
    render(
      <ExplanationPanel document={document} activeChapter="chapter1" onChapterChange={vi.fn()} />,
    )

    expect(screen.getByRole('tablist')).toBeInTheDocument()
    expect(screen.getAllByRole('tab')).toHaveLength(7)
    expect(screen.getByRole('tab', { name: 'What This Code Does' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Common Mistakes' })).toBeInTheDocument()
  })

  it('should mark the active chapter tab as selected', () => {
    render(
      <ExplanationPanel document={document} activeChapter="chapter2" onChapterChange={vi.fn()} />,
    )

    expect(screen.getByRole('tab', { name: 'Prerequisites Knowledge' })).toHaveAttribute(
      'aria-selected',
      'true',
    )
  })

  it('should call onChapterChange when a chapter tab is clicked', () => {
    const handleChange = vi.fn()
    render(
      <ExplanationPanel document={document} activeChapter="chapter1" onChapterChange={handleChange} />,
    )

    fireEvent.click(screen.getByRole('tab', { name: 'Core Concepts Summary' }))

    expect(handleChange).toHaveBeenCalledWith('chapter6')
  })

  it('should render Chapter1Summary content for chapter1', () => {
    render(
      <ExplanationPanel document={document} activeChapter="chapter1" onChapterChange={vi.fn()} />,
    )

    expect(screen.getByText('It adds numbers.')).toBeInTheDocument()
  })

  it('should render Chapter2Prerequisites content for chapter2', () => {
    render(
      <ExplanationPanel document={document} activeChapter="chapter2" onChapterChange={vi.fn()} />,
    )

    expect(screen.getByText('Variables')).toBeInTheDocument()
  })

  it('should render chapter3 content inline (flowchart and file breakdown)', () => {
    render(
      <ExplanationPanel document={document} activeChapter="chapter3" onChapterChange={vi.fn()} />,
    )

    expect(screen.getByText(/flowchart TD/)).toBeInTheDocument()
    expect(screen.getByText(/Entry point\./)).toBeInTheDocument()
  })

  it('should render Chapter4LineByLine content for chapter4 and forward activeExplanationIndex', () => {
    render(
      <ExplanationPanel
        document={document}
        activeChapter="chapter4"
        onChapterChange={vi.fn()}
        activeExplanationIndex={0}
      />,
    )

    const items = screen.getAllByRole('listitem')
    expect(items[0]).toHaveAttribute('aria-current', 'true')
  })

  it('should render chapter5 content inline (steps)', () => {
    render(
      <ExplanationPanel document={document} activeChapter="chapter5" onChapterChange={vi.fn()} />,
    )

    expect(screen.getByText('x is set to 1.')).toBeInTheDocument()
  })

  it('should render chapter6 content inline (core concepts)', () => {
    render(
      <ExplanationPanel document={document} activeChapter="chapter6" onChapterChange={vi.fn()} />,
    )

    expect(screen.getByText('Assignment')).toBeInTheDocument()
  })

  it('should render chapter7 content inline (common mistakes)', () => {
    render(
      <ExplanationPanel document={document} activeChapter="chapter7" onChapterChange={vi.fn()} />,
    )

    expect(screen.getByText('Syntax error.')).toBeInTheDocument()
  })
})
