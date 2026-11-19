import type { KeyboardEvent } from 'react'

import type { Project } from '../../services/project-service'

export interface ProjectCardProps {
  project: Project
  onClick?: (project: Project) => void
}

export function ProjectCard({ project, onClick }: ProjectCardProps) {
  function handleKeyDown(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key === 'Enter') {
      onClick?.(project)
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onClick?.(project)}
      onKeyDown={handleKeyDown}
    >
      <h3>{project.title}</h3>
      <p>{project.description || '설명이 없습니다'}</p>
      <p>Last activity: {project.last_activity_at}</p>
    </div>
  )
}
