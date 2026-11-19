import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

// ProjectCard (T051) does not exist yet — frontend/src/components/project/ProjectCard.tsx
//
// Expected contract:
//   export interface ProjectCardProps {
//     project: Project  // from @/services/project-service
//     onClick?: (project: Project) => void
//   }
//   export function ProjectCard({ project, onClick }: ProjectCardProps)
//
// Design decisions (documented for the GREEN-phase implementer):
//   - ProjectCard is a plain presentational component. It does NOT navigate
//     itself and does NOT import react-router-dom's Link — it is rendered as
//     a clickable element (role="button", keyboard-activatable) that calls
//     the `onClick` prop with the full `project` object. The caller (Dashboard)
//     owns navigation, e.g. onClick={(p) => navigate(`/projects/${p.id}`)}.
//   - project.title renders in a heading (role="heading").
//   - project.description renders as plain text; when null/empty, a fixed
//     Korean placeholder "설명이 없습니다" is shown instead (progress-tracking
//     task-completion counts don't exist yet per tasks.md, so this is the
//     "minimal placeholder" called for in the task — last_activity_at is
//     shown verbatim, no date formatting, to keep the contract locale-free).
//   - last_activity_at renders verbatim (no Date parsing) inside text that
//     contains the literal string "Last activity:" followed by the raw value,
//     so tests can match on substring without fighting timezone formatting.
import { ProjectCard } from '@/components/project/ProjectCard'
import type { Project } from '@/services/project-service'

const baseProject: Project = {
  id: 'project-1',
  title: 'My First Project',
  description: 'Learning FastAPI',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  last_activity_at: '2026-01-02T00:00:00Z',
}

describe('ProjectCard', () => {
  it('should render the project title', () => {
    render(<ProjectCard project={baseProject} />)

    expect(screen.getByText('My First Project')).toBeInTheDocument()
  })

  it('should render the project description', () => {
    render(<ProjectCard project={baseProject} />)

    expect(screen.getByText('Learning FastAPI')).toBeInTheDocument()
  })

  it('should render a placeholder when the description is null', () => {
    render(<ProjectCard project={{ ...baseProject, description: null }} />)

    expect(screen.getByText('설명이 없습니다')).toBeInTheDocument()
  })

  it('should render the last_activity_at value', () => {
    render(<ProjectCard project={baseProject} />)

    expect(screen.getByText(/Last activity:/i)).toHaveTextContent('2026-01-02T00:00:00Z')
  })

  it('should call onClick with the project when clicked', () => {
    const handleClick = vi.fn()
    render(<ProjectCard project={baseProject} onClick={handleClick} />)

    fireEvent.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledWith(baseProject)
  })

  it('should call onClick with the project when activated via keyboard (Enter)', () => {
    const handleClick = vi.fn()
    render(<ProjectCard project={baseProject} onClick={handleClick} />)

    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter', code: 'Enter' })

    expect(handleClick).toHaveBeenCalledWith(baseProject)
  })

  it('should not throw when clicked without an onClick prop', () => {
    render(<ProjectCard project={baseProject} />)

    expect(() => fireEvent.click(screen.getByRole('button'))).not.toThrow()
  })
})
