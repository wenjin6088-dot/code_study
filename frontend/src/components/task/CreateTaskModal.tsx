import { useState } from 'react'

import { Button } from '../ui/button'
import { FileUpload } from '../upload/FileUpload'
import { FolderUpload } from '../upload/FolderUpload'
import { LANGUAGE_OPTIONS, PasteCode } from '../upload/PasteCode'
import { createTask, type Task } from '../../services/task-service'

export interface CreateTaskModalProps {
  isOpen: boolean
  projectId: string
  onClose: () => void
  onCreate: (task: Task) => void
}

type UploadMethod = 'file' | 'folder' | 'paste'

export function CreateTaskModal({ isOpen, projectId, onClose, onCreate }: CreateTaskModalProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [uploadMethod, setUploadMethod] = useState<UploadMethod>('file')
  const [files, setFiles] = useState<File[]>([])
  const [pasteContent, setPasteContent] = useState('')
  const [pasteLanguage, setPasteLanguage] = useState(LANGUAGE_OPTIONS[0].value)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) {
    return null
  }

  function switchMethod(method: UploadMethod) {
    setUploadMethod(method)
    setFiles([])
    setPasteContent('')
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    setError(null)
    setIsSubmitting(true)
    try {
      const trimmedDescription = description.trim()
      const sharedFields = {
        title,
        description: trimmedDescription ? description : undefined,
      }

      const task =
        uploadMethod === 'paste'
          ? await createTask(projectId, {
              ...sharedFields,
              uploadMethod: 'paste',
              pasteContent,
              pasteFilename:
                LANGUAGE_OPTIONS.find((opt) => opt.value === pasteLanguage)?.filename ??
                'pasted.txt',
            })
          : await createTask(projectId, {
              ...sharedFields,
              uploadMethod,
              files,
            })

      onCreate(task)
    } catch (err) {
      setError(err instanceof Error ? err.message : '작업 생성에 실패했습니다')
    } finally {
      setIsSubmitting(false)
    }
  }

  const isTitleTooShort = title.trim().length < 5
  const isUploadEmpty = uploadMethod === 'paste' ? pasteContent === '' : files.length === 0
  const isSubmitDisabled = isTitleTooShort || isUploadEmpty || isSubmitting

  return (
    <div role="dialog">
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="create-task-title">Title</label>
          <input
            id="create-task-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="create-task-description">Description</label>
          <input
            id="create-task-description"
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <div>
          <Button
            type="button"
            variant={uploadMethod === 'file' ? 'default' : 'outline'}
            onClick={() => switchMethod('file')}
          >
            파일
          </Button>
          <Button
            type="button"
            variant={uploadMethod === 'folder' ? 'default' : 'outline'}
            onClick={() => switchMethod('folder')}
          >
            폴더
          </Button>
          <Button
            type="button"
            variant={uploadMethod === 'paste' ? 'default' : 'outline'}
            onClick={() => switchMethod('paste')}
          >
            붙여넣기
          </Button>
        </div>
        {uploadMethod === 'file' && <FileUpload onFilesSelected={setFiles} />}
        {uploadMethod === 'folder' && <FolderUpload onFilesSelected={setFiles} />}
        {uploadMethod === 'paste' && (
          <PasteCode
            content={pasteContent}
            onContentChange={setPasteContent}
            language={pasteLanguage}
            onLanguageChange={setPasteLanguage}
          />
        )}
        {error && <p role="alert">{error}</p>}
        <Button type="submit" disabled={isSubmitDisabled}>
          Create
        </Button>
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
      </form>
    </div>
  )
}
