import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useParams } from 'react-router-dom'

import { DocumentViewer } from '../components/document/DocumentViewer'
import { PracticeViewer } from '../components/practice/PracticeViewer'
import { getTask } from '../services/task-service'

const TABS = ['Document', 'Practice', 'Q&A'] as const
type Tab = (typeof TABS)[number]

function TaskDetail() {
  const { taskId } = useParams<{ projectId: string; taskId: string }>()
  const [activeTab, setActiveTab] = useState<Tab>('Document')

  const { data: task, isLoading, isError } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => getTask(taskId as string),
  })

  if (isLoading) {
    return <div role="status">Loading...</div>
  }

  if (isError || !task) {
    return <p>작업을 찾을 수 없습니다</p>
  }

  return (
    <div>
      <h1>{task.title}</h1>
      <div role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={activeTab === tab}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>
      <div role="tabpanel">
        {activeTab === 'Document' && <DocumentViewer taskId={taskId as string} />}
        {activeTab === 'Practice' && <PracticeViewer taskId={taskId as string} />}
        {activeTab === 'Q&A' && <p>Q&A 탭 (준비 중)</p>}
      </div>
    </div>
  )
}

export default TaskDetail
