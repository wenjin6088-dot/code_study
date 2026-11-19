import { useState } from 'react'

import { Button } from '../ui/button'
import type { Project } from '../../services/project-service'
import { permanentDeleteProject, restoreProject } from '../../services/trash-service'

export interface TrashedProjectCardProps {
  project: Project
  onRestore: (project: Project) => void
  onPermanentDelete: (project: Project) => void
}

export function TrashedProjectCard({
  project,
  onRestore,
  onPermanentDelete,
}: TrashedProjectCardProps) {
  const [isConfirming, setIsConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isBusy, setIsBusy] = useState(false)

  async function handleRestore() {
    setError(null)
    setIsBusy(true)
    try {
      const restored = await restoreProject(project.id)
      onRestore(restored)
    } catch (err) {
      setError(err instanceof Error ? err.message : '복원에 실패했습니다')
    } finally {
      setIsBusy(false)
    }
  }

  async function handleConfirmPermanentDelete() {
    setError(null)
    setIsBusy(true)
    try {
      await permanentDeleteProject(project.id)
      onPermanentDelete(project)
    } catch (err) {
      setError(err instanceof Error ? err.message : '삭제에 실패했습니다')
    } finally {
      setIsBusy(false)
    }
  }

  return (
    <div>
      <h3>{project.title}</h3>
      <p>{project.description || '설명이 없습니다'}</p>
      {error && <p role="alert">{error}</p>}
      {isConfirming ? (
        <div>
          <p>정말 영구적으로 삭제하시겠습니까?</p>
          <Button
            type="button"
            variant="destructive"
            disabled={isBusy}
            onClick={handleConfirmPermanentDelete}
          >
            확인
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setIsConfirming(false)
              setError(null)
            }}
          >
            취소
          </Button>
        </div>
      ) : (
        <div>
          <Button type="button" disabled={isBusy} onClick={handleRestore}>
            복원
          </Button>
          <Button type="button" variant="destructive" onClick={() => setIsConfirming(true)}>
            영구 삭제
          </Button>
        </div>
      )}
    </div>
  )
}
