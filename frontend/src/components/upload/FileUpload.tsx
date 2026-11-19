import { useRef, type ChangeEvent, type DragEvent } from 'react'

import { Button } from '../ui/button'

export interface FileUploadProps {
  onFilesSelected: (files: File[]) => void
}

export function FileUpload({ onFilesSelected }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    if (e.target.files) {
      onFilesSelected(Array.from(e.target.files))
    }
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    if (e.dataTransfer.files) {
      onFilesSelected(Array.from(e.dataTransfer.files))
    }
  }

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
  }

  return (
    <div data-testid="file-upload-dropzone" onDrop={handleDrop} onDragOver={handleDragOver}>
      <p>이 영역에 파일을 드래그하세요</p>
      <input
        ref={inputRef}
        data-testid="file-upload-input"
        type="file"
        multiple
        onChange={handleChange}
        style={{ display: 'none' }}
      />
      <Button type="button" onClick={() => inputRef.current?.click()}>
        파일 선택
      </Button>
    </div>
  )
}
