import Editor, { type OnMount } from '@monaco-editor/react'
import { useEffect, useRef } from 'react'

import type { TaskCodeFile } from '../../services/task-service'
import { getMonacoLanguage } from './monacoConfig'

export interface HighlightRange {
  file: string
  lineStart: number
  lineEnd: number
}

export interface CodePanelProps {
  files: TaskCodeFile[]
  activeFilePath: string
  onActiveFileChange?: (filePath: string) => void
  onVisibleLineChange?: (filePath: string, lineNumber: number) => void
  highlightRange?: HighlightRange | null
}

function filePathOf(file: TaskCodeFile): string {
  return file.file_path ?? file.file_name
}

export function CodePanel({
  files,
  activeFilePath,
  onActiveFileChange,
  onVisibleLineChange,
  highlightRange,
}: CodePanelProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const editorRef = useRef<any>(null)
  const decorationIdsRef = useRef<string[]>([])

  const activeFile = files.find((file) => filePathOf(file) === activeFilePath) ?? files[0]

  const handleMount: OnMount = (editor) => {
    editorRef.current = editor
    editor.onDidScrollChange(() => {
      const visibleRanges = editor.getVisibleRanges?.()
      const startLine = visibleRanges?.[0]?.startLineNumber
      if (startLine != null && activeFile) {
        onVisibleLineChange?.(filePathOf(activeFile), startLine)
      }
    })
  }

  useEffect(() => {
    const editor = editorRef.current
    if (!editor || !activeFile) {
      return
    }
    if (highlightRange && highlightRange.file === filePathOf(activeFile)) {
      editor.revealLineInCenter?.(highlightRange.lineStart)
      decorationIdsRef.current =
        editor.deltaDecorations?.(decorationIdsRef.current, [
          {
            range: {
              startLineNumber: highlightRange.lineStart,
              startColumn: 1,
              endLineNumber: highlightRange.lineEnd,
              endColumn: 1,
            },
            options: { isWholeLine: true, className: 'code-panel-highlight-line' },
          },
        ]) ?? []
    } else if (decorationIdsRef.current.length > 0) {
      decorationIdsRef.current = editor.deltaDecorations?.(decorationIdsRef.current, []) ?? []
    }
  }, [highlightRange, activeFile])

  if (!activeFile) {
    return <p>표시할 코드가 없습니다</p>
  }

  return (
    <div>
      {files.length > 1 && (
        <div role="tablist">
          {files.map((file) => {
            const path = filePathOf(file)
            return (
              <button
                key={path}
                type="button"
                role="tab"
                aria-selected={path === activeFilePath}
                onClick={() => onActiveFileChange?.(path)}
              >
                {file.file_name}
              </button>
            )
          })}
        </div>
      )}
      <Editor
        key={filePathOf(activeFile)}
        height="100%"
        language={getMonacoLanguage(activeFile.file_extension)}
        value={activeFile.content}
        onMount={handleMount}
        options={{ readOnly: true, lineNumbers: 'on' }}
      />
    </div>
  )
}
