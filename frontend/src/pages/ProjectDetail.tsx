import { useQueryClient, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { Button } from '../components/ui/button'
import { CreateTaskModal } from '../components/task/CreateTaskModal'
import { TaskCard } from '../components/task/TaskCard'
import {
  getProject,
  removeProject,
  updateProject,
  type Project,
} from '../services/project-service'
import { listTasks, type Task } from '../services/task-service'

function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isEditing, setIsEditing] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false)

  const { data: project, isLoading, isError } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId as string),
  })

  const { data: tasks } = useQuery({
    queryKey: ['tasks', projectId],
    queryFn: () => listTasks(projectId as string),
  })

  if (isLoading) {
    return <div role="status">Loading...</div>
  }

  if (isError || !project) {
    return <p>프로젝트를 찾을 수 없습니다</p>
  }

  function startEditing() {
    setTitle(project!.title)
    setDescription(project!.description ?? '')
    setError(null)
    setIsEditing(true)
  }

  function cancelEditing() {
    setIsEditing(false)
    setError(null)
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()

    setError(null)
    setIsSaving(true)
    try {
      const trimmedDescription = description.trim()
      const updated = await updateProject(projectId as string, {
        title,
        description: trimmedDescription ? description : undefined,
      })
      queryClient.setQueryData<Project>(['project', projectId], updated)
      setIsEditing(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : '프로젝트 수정에 실패했습니다')
    } finally {
      setIsSaving(false)
    }
  }

  async function handleConfirmDelete() {
    setDeleteError(null)
    setIsDeleting(true)
    try {
      await removeProject(projectId as string)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate('/')
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : '삭제에 실패했습니다')
    } finally {
      setIsDeleting(false)
    }
  }

  function handleTaskCreated(_task: Task) {
    setIsTaskModalOpen(false)
    queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
  }

  const isTitleEmpty = title.trim().length === 0

  const tasksSection = (
    <>
      <h2>Tasks</h2>
      <Button type="button" onClick={() => setIsTaskModalOpen(true)}>
        작업 추가
      </Button>
      {!tasks || tasks.length === 0 ? (
        <p>아직 작업이 없습니다</p>
      ) : (
        <ul>
          {tasks.map((task) => (
            <li key={task.id}>
              <TaskCard
                task={task}
                onClick={(t) => navigate(`/projects/${projectId}/tasks/${t.id}`)}
              />
            </li>
          ))}
        </ul>
      )}
      <CreateTaskModal
        isOpen={isTaskModalOpen}
        projectId={projectId as string}
        onClose={() => setIsTaskModalOpen(false)}
        onCreate={handleTaskCreated}
      />
    </>
  )

  if (isEditing) {
    return (
      <div>
        <form onSubmit={handleSave}>
          <div>
            <label htmlFor="edit-project-title">Title</label>
            <input
              id="edit-project-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="edit-project-description">Description</label>
            <input
              id="edit-project-description"
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          {error && <p role="alert">{error}</p>}
          <Button type="submit" disabled={isTitleEmpty || isSaving}>
            Save
          </Button>
          <Button type="button" variant="outline" onClick={cancelEditing}>
            Cancel
          </Button>
        </form>
        {tasksSection}
      </div>
    )
  }

  return (
    <div>
      <h1>{project.title}</h1>
      <p>{project.description || '설명이 없습니다'}</p>
      <Button onClick={startEditing}>Edit</Button>
      {deleteError && <p role="alert">{deleteError}</p>}
      {isConfirmingDelete ? (
        <div>
          <p>정말 삭제하시겠습니까?</p>
          <Button
            type="button"
            variant="destructive"
            disabled={isDeleting}
            onClick={handleConfirmDelete}
          >
            확인
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setIsConfirmingDelete(false)
              setDeleteError(null)
            }}
          >
            취소
          </Button>
        </div>
      ) : (
        <Button variant="destructive" onClick={() => setIsConfirmingDelete(true)}>
          Delete
        </Button>
      )}
      {tasksSection}
    </div>
  )
}

export default ProjectDetail
