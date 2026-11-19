import { useState } from 'react'

import { Button } from '../ui/button'
import { createProject, type Project } from '../../services/project-service'

export interface CreateProjectModalProps {
  isOpen: boolean
  onClose: () => void
  onCreate: (project: Project) => void
}

export function CreateProjectModal({ isOpen, onClose, onCreate }: CreateProjectModalProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) {
    return null
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    setError(null)
    setIsSubmitting(true)
    try {
      const trimmedDescription = description.trim()
      const project = await createProject({
        title,
        description: trimmedDescription ? description : undefined,
      })
      onCreate(project)
    } catch (err) {
      setError(err instanceof Error ? err.message : '프로젝트 생성에 실패했습니다')
    } finally {
      setIsSubmitting(false)
    }
  }

  const isTitleEmpty = title.trim().length === 0

  return (
    <div role="dialog">
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="create-project-title">Title</label>
          <input
            id="create-project-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="create-project-description">Description</label>
          <input
            id="create-project-description"
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        {error && <p role="alert">{error}</p>}
        <Button type="submit" disabled={isTitleEmpty || isSubmitting}>
          Create
        </Button>
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
      </form>
    </div>
  )
}
