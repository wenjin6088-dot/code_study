import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { getTaskDocument, getTaskDocumentStatus } from '../../services/document-service'
import { getTaskCode } from '../../services/task-service'
import { CodePanel, type HighlightRange } from './CodePanel'
import { ExplanationPanel, type ChapterKey } from './ExplanationPanel'
import { findExplanationForLine } from './syncScroll'

export interface DocumentViewerProps {
  taskId: string
}

const POLL_INTERVAL_MS = 3000

export function DocumentViewer({ taskId }: DocumentViewerProps) {
  const [activeChapter, setActiveChapter] = useState<ChapterKey>('chapter1')
  const [activeFilePath, setActiveFilePath] = useState<string | null>(null)
  const [activeExplanationIndex, setActiveExplanationIndex] = useState<number | undefined>(
    undefined,
  )

  const statusQuery = useQuery({
    queryKey: ['taskDocumentStatus', taskId],
    queryFn: () => getTaskDocumentStatus(taskId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'pending' || status === 'in_progress' ? POLL_INTERVAL_MS : false
    },
  })

  const isCompleted = statusQuery.data?.status === 'completed'

  const documentQuery = useQuery({
    queryKey: ['taskDocument', taskId],
    queryFn: () => getTaskDocument(taskId),
    enabled: isCompleted,
  })

  const codeQuery = useQuery({
    queryKey: ['taskCode', taskId],
    queryFn: () => getTaskCode(taskId),
    enabled: isCompleted,
  })

  if (statusQuery.isLoading) {
    return <div role="status">문서 상태를 확인하는 중...</div>
  }

  if (statusQuery.isError) {
    return <p>문서를 찾을 수 없습니다</p>
  }

  if (statusQuery.data?.status === 'failed') {
    return (
      <div role="alert">
        <p>문서 생성에 실패했습니다.</p>
        {statusQuery.data.error && <p>{statusQuery.data.error}</p>}
      </div>
    )
  }

  if (statusQuery.data?.status === 'pending' || statusQuery.data?.status === 'in_progress') {
    return (
      <div role="status">
        <p>문서를 생성하는 중입니다...</p>
        {statusQuery.data.estimated_seconds_remaining != null && (
          <p>예상 남은 시간: {statusQuery.data.estimated_seconds_remaining}초</p>
        )}
      </div>
    )
  }

  if (!documentQuery.data?.content || !codeQuery.data) {
    return <div role="status">문서를 불러오는 중...</div>
  }

  const content = documentQuery.data.content
  const files = codeQuery.data.files
  const currentFilePath = activeFilePath ?? files[0]?.file_name ?? ''

  function handleVisibleLineChange(filePath: string, lineNumber: number) {
    const index = findExplanationForLine(content.chapter4.explanations, filePath, lineNumber)
    if (index >= 0) {
      setActiveExplanationIndex(index)
      setActiveChapter('chapter4')
    }
  }

  const activeExplanation =
    activeExplanationIndex != null ? content.chapter4.explanations[activeExplanationIndex] : null
  const highlightRange: HighlightRange | null = activeExplanation
    ? {
        file: activeExplanation.file,
        lineStart: activeExplanation.line_start,
        lineEnd: activeExplanation.line_end,
      }
    : null

  return (
    <div style={{ display: 'flex', gap: '1rem' }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <CodePanel
          files={files}
          activeFilePath={currentFilePath}
          onActiveFileChange={setActiveFilePath}
          onVisibleLineChange={handleVisibleLineChange}
          highlightRange={highlightRange}
        />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <ExplanationPanel
          document={content}
          activeChapter={activeChapter}
          onChapterChange={setActiveChapter}
          activeExplanationIndex={activeChapter === 'chapter4' ? activeExplanationIndex : undefined}
        />
      </div>
    </div>
  )
}
