import type { KeyboardEvent } from 'react'

import type { Task } from '../../services/task-service'

export interface TaskCardProps {
  task: Task
  onClick?: (task: Task) => void
}

export function TaskCard({ task, onClick }: TaskCardProps) {
  function handleKeyDown(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key === 'Enter') {
      onClick?.(task)
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onClick?.(task)}
      onKeyDown={handleKeyDown}
    >
      <h3>
        Task {task.task_number}: {task.title}
      </h3>
      <p>{task.description || '설명이 없습니다'}</p>
      {task.uploaded_code && (
        <div>
          {task.uploaded_code.detected_language && (
            <span>{task.uploaded_code.detected_language}</span>
          )}
          {task.uploaded_code.complexity_level && (
            <span>{task.uploaded_code.complexity_level}</span>
          )}
          {task.upload_method && <span>{task.upload_method}</span>}
        </div>
      )}
    </div>
  )
}
