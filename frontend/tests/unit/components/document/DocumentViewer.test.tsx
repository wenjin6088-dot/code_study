import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// DocumentViewer (T105/T106/T107) does not exist yet —
// frontend/src/components/document/DocumentViewer.tsx
//
// Composes CodePanel + ExplanationPanel into a 2-column layout, fetches the
// task's document (polling /document/status while pending/in_progress, FR-084)
// and source code, shows a loading/progress state, and drives the
// one-direction sync scroll: when CodePanel reports a visible line, look up
// the matching chapter4 explanation (syncScroll.ts) and switch
// ExplanationPanel to chapter4, highlighting that entry.
//
// CodePanel and ExplanationPanel are mocked here because their own rendering
// is already covered by their dedicated unit tests; this file only tests
// DocumentViewer's data-fetching and wiring responsibilities.
vi.mock('@/components/document/CodePanel', () => ({
  CodePanel: (props: { onVisibleLineChange?: (file: string, line: number) => void }) => (
    <div data-testid="code-panel">
      <button type="button" onClick={() => props.onVisibleLineChange?.('main.py', 1)}>
        simulate-scroll
      </button>
    </div>
  ),
}))

vi.mock('@/components/document/ExplanationPanel', () => ({
  ExplanationPanel: (props: { activeChapter: string; activeExplanationIndex?: number }) => (
    <div data-testid="explanation-panel">
      <span data-testid="active-chapter">{props.activeChapter}</span>
      <span data-testid="active-explanation-index">{String(props.activeExplanationIndex)}</span>
    </div>
  ),
}))

import { DocumentViewer } from '@/components/document/DocumentViewer'
import { getTaskDocument, getTaskDocumentStatus } from '@/services/document-service'
import { getTaskCode } from '@/services/task-service'
import { createTestQueryClient } from '../../../test-utils/queryClient'

vi.mock('@/services/document-service')
vi.mock('@/services/task-service')

const mockedGetTaskDocument = getTaskDocument as unknown as ReturnType<typeof vi.fn>
const mockedGetTaskDocumentStatus = getTaskDocumentStatus as unknown as ReturnType<typeof vi.fn>
const mockedGetTaskCode = getTaskCode as unknown as ReturnType<typeof vi.fn>

const content = {
  chapter1: { title: 'What This Code Does', summary: 'It adds numbers.' },
  chapter2: { title: 'Prerequisites Knowledge', concepts: [] },
  chapter3: { title: 'Code Structure Overview', flowchart: '', file_breakdown: {} },
  chapter4: {
    title: 'Line-by-Line Explanation',
    explanations: [
      {
        file: 'main.py',
        line_start: 1,
        line_end: 2,
        code: 'x = 1',
        what_it_does: '',
        syntax_breakdown: '',
        analogy: '',
        alternative_example: '',
        notes: '',
      },
    ],
  },
  chapter5: { title: 'Execution Flow Simulation', steps: [] },
  chapter6: { title: 'Core Concepts Summary', concepts: [] },
  chapter7: { title: 'Common Mistakes', mistakes: [] },
}

function renderViewer(taskId = 'task-1') {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <DocumentViewer taskId={taskId} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  mockedGetTaskDocument.mockReset()
  mockedGetTaskDocumentStatus.mockReset()
  mockedGetTaskCode.mockReset()
})

describe('DocumentViewer', () => {
  it('should show a loading state while the document status is being fetched', () => {
    mockedGetTaskDocumentStatus.mockReturnValue(new Promise(() => {}))

    renderViewer()

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('should show the estimated remaining time while the document is in_progress', async () => {
    mockedGetTaskDocumentStatus.mockResolvedValue({
      status: 'in_progress',
      error: null,
      estimated_seconds_remaining: 37,
    })

    renderViewer()

    expect(await screen.findByText(/37/)).toBeInTheDocument()
  })

  it('should show a failure message when document generation failed', async () => {
    mockedGetTaskDocumentStatus.mockResolvedValue({
      status: 'failed',
      error: 'AI 서비스 오류',
      estimated_seconds_remaining: null,
    })

    renderViewer()

    expect(await screen.findByText(/AI 서비스 오류/)).toBeInTheDocument()
  })

  it('should render CodePanel and ExplanationPanel once completed', async () => {
    mockedGetTaskDocumentStatus.mockResolvedValue({
      status: 'completed',
      error: null,
      estimated_seconds_remaining: null,
    })
    mockedGetTaskDocument.mockResolvedValue({
      task_id: 'task-1',
      status: 'completed',
      content,
      error: null,
      generated_at: '2026-01-01T00:00:00Z',
    })
    mockedGetTaskCode.mockResolvedValue({
      files: [{ file_name: 'main.py', file_path: 'main.py', file_extension: '.py', content: 'x = 1\ny = 2\n' }],
    })

    renderViewer()

    expect(await screen.findByTestId('code-panel')).toBeInTheDocument()
    expect(screen.getByTestId('explanation-panel')).toBeInTheDocument()
  })

  it('should switch to chapter4 and highlight the matching explanation when the code panel scrolls', async () => {
    mockedGetTaskDocumentStatus.mockResolvedValue({
      status: 'completed',
      error: null,
      estimated_seconds_remaining: null,
    })
    mockedGetTaskDocument.mockResolvedValue({
      task_id: 'task-1',
      status: 'completed',
      content,
      error: null,
      generated_at: '2026-01-01T00:00:00Z',
    })
    mockedGetTaskCode.mockResolvedValue({
      files: [{ file_name: 'main.py', file_path: 'main.py', file_extension: '.py', content: 'x = 1\ny = 2\n' }],
    })

    renderViewer()

    const scrollButton = await screen.findByText('simulate-scroll')
    fireEvent.click(scrollButton)

    expect(screen.getByTestId('active-chapter')).toHaveTextContent('chapter4')
    expect(screen.getByTestId('active-explanation-index')).toHaveTextContent('0')
  })
})
