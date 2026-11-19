import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// CodePanel (T100) does not exist yet — frontend/src/components/document/CodePanel.tsx
//
// Wraps @monaco-editor/react in read-only mode to display the task's source
// files (from getTaskCode) with syntax highlighting (T099). It also reports
// the line number currently scrolled into view via onVisibleLineChange, which
// DocumentViewer (T105) uses to drive the one-direction sync scroll into
// ExplanationPanel.
//
// @monaco-editor/react is mocked below: jsdom cannot run the real Monaco
// editor, and this component's own tests only need to assert on the props
// CodePanel passes to <Editor>, not on Monaco's internals.
const { mockEditor, getScrollCallback } = vi.hoisted(() => {
  let scrollCallback: (() => void) | null = null
  const mockEditor = {
    onDidScrollChange: (cb: () => void) => {
      scrollCallback = cb
    },
    getVisibleRanges: vi.fn(() => [{ startLineNumber: 42 }]),
    revealLineInCenter: vi.fn(),
    deltaDecorations: vi.fn(() => ['decoration-1']),
  }
  return { mockEditor, getScrollCallback: () => scrollCallback }
})

vi.mock('@monaco-editor/react', () => ({
  default: (props: { value: string; language: string; onMount?: (editor: unknown) => void }) => {
    props.onMount?.(mockEditor)
    return (
      <div data-testid="monaco-editor" data-language={props.language}>
        <pre data-testid="monaco-value">{props.value}</pre>
      </div>
    )
  },
}))

import { CodePanel } from '@/components/document/CodePanel'
import type { TaskCodeFile } from '@/services/task-service'

const files: TaskCodeFile[] = [
  { file_name: 'main.py', file_path: 'main.py', file_extension: '.py', content: 'x = 1\ny = 2\n' },
  { file_name: 'utils.py', file_path: 'utils.py', file_extension: '.py', content: 'def f(): pass\n' },
]

beforeEach(() => {
  mockEditor.revealLineInCenter.mockClear()
  mockEditor.deltaDecorations.mockClear()
})

describe('CodePanel', () => {
  it('should render the active file content through the Monaco editor with the mapped language', () => {
    render(<CodePanel files={files} activeFilePath="main.py" />)

    expect(screen.getByTestId('monaco-editor')).toHaveAttribute('data-language', 'python')
    expect(screen.getByTestId('monaco-value')).toHaveTextContent('x = 1')
  })

  it('should render a tab per file and call onActiveFileChange when switching', () => {
    const handleChange = vi.fn()
    render(<CodePanel files={files} activeFilePath="main.py" onActiveFileChange={handleChange} />)

    const tabs = screen.getAllByRole('tab')
    expect(tabs).toHaveLength(2)

    fireEvent.click(screen.getByRole('tab', { name: 'utils.py' }))

    expect(handleChange).toHaveBeenCalledWith('utils.py')
  })

  it('should not render file tabs when there is only one file', () => {
    render(<CodePanel files={[files[0]]} activeFilePath="main.py" />)

    expect(screen.queryByRole('tab')).not.toBeInTheDocument()
  })

  it('should report the visible line number for the active file when the editor scrolls', () => {
    const handleVisibleLineChange = vi.fn()
    render(
      <CodePanel
        files={files}
        activeFilePath="main.py"
        onVisibleLineChange={handleVisibleLineChange}
      />,
    )

    getScrollCallback()?.()

    expect(handleVisibleLineChange).toHaveBeenCalledWith('main.py', 42)
  })

  it('should reveal and decorate the highlighted range when it matches the active file', () => {
    render(
      <CodePanel
        files={files}
        activeFilePath="main.py"
        highlightRange={{ file: 'main.py', lineStart: 2, lineEnd: 2 }}
      />,
    )

    expect(mockEditor.revealLineInCenter).toHaveBeenCalledWith(2)
    expect(mockEditor.deltaDecorations).toHaveBeenCalled()
  })
})
